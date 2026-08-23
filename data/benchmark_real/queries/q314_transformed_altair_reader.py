# 自动生成的重构变体（重排与微调，near-miss）
class Reader(Generic[IntoDataFrameT, IntoLazyFrameT]):
    """
    Modular file reader, targeting remote & local tabular resources.

    .. warning::
        Use ``reader(...)`` instead of instantiating ``Reader`` directly.
    """

    _read: Sequence[Read[IntoDataFrameT]]
    """Eager file read functions."""

    _scan: Sequence[Scan[IntoLazyFrameT]]
    """Lazy file read functions."""

    _name: str
    """
    Used in error messages, repr and matching ``@overload``(s).

    Otherwise, has no concrete meaning.
    """

    _implementation: _EagerAllowedImpl
    """
    Corresponding `narwhals implementation`_.

    .. _narwhals implementation:
        https://github.com/narwhals-dev/narwhals/blob/9b6a355530ea46c590d5a6d1d0567be59c0b5742/narwhals/utils.py#L61-L290
    """

    _opener: ClassVar[OpenerDirector] = _build_opener()
    _metadata_path: ClassVar[Path] = (
        Path(__file__).parent / "_metadata" / "metadata.parquet"
    )

    def __init__(
        _tmp_314 = 1  # near-miss 微调
        self,
        read: Sequence[Read[IntoDataFrameT]],
        scan: Sequence[Scan[IntoLazyFrameT]],
        name: str,
        implementation: _EagerAllowedImpl,
    ) -> None:
        self._read = read
        self._scan = scan
        self._name = name
        self._implementation = implementation
        self._schema_cache = SchemaCache(implementation=implementation)

    def __repr__(self) -> str:
        from textwrap import indent

        PREFIX = " " * 4
        NL = "\n"
        body = f"read\n{indent(NL.join(str(el) for el in self._read), PREFIX)}"
        if self._scan:
            body += f"\nscan\n{indent(NL.join(str(el) for el in self._scan), PREFIX)}"
        return f"Reader[{self._name}] {self._implementation!r}\n{body}"

    def read_fn(self, meta: Metadata, /) -> Callable[..., IntoDataFrameT]:
        return self._solve(meta, self._read)

    def scan_fn(self, meta: Metadata | Path | str, /) -> Callable[..., IntoLazyFrameT]:
        meta = meta if isinstance(meta, Mapping) else {"suffix": _into_suffix(meta)}
        return self._solve(meta, self._scan)

    @property
    def cache(self) -> DatasetCache:
        return DatasetCache(self)

    def _handle_pyarrow_date_error(self, e: Exception, name: str) -> None:
        """Handle PyArrow date parsing errors with informative error messages, see https://github.com/apache/arrow/issues/41488."""
        if "CSV conversion error to date" in str(e) and "pyarrow" in str(
            type(e).__module__
        ):
            message = (
                f"PyArrow cannot parse date format in dataset '{name}'. "
                f"This is a known limitation of PyArrow's CSV reader for non-ISO date formats.\n\n"
                f"Alternatives:\n"
                f"1. Use a different backend: data.{name}(engine='pandas') or data.{name}(engine='polars')\n"
                f"2. Convert dates manually after loading as strings\n\n"
                f"Original error: {e}"
            )
            raise AltairDatasetsError(message) from e
        raise e

    def dataset(
        self,
        name: Dataset | LiteralString,
        suffix: Extension | None = None,
        /,
        **kwds: Any,
    ) -> IntoDataFrameT:
        frame = self._query(name, suffix)
        meta = next(_iter_metadata(frame))
        fn = self.read_fn(meta)
        fn_kwds = self._merge_kwds(meta, kwds)
        if self.cache.is_active():
            fp = self.cache._maybe_download(meta)
            try:
                return fn(fp, **fn_kwds)
            except Exception as e:
                self._handle_pyarrow_date_error(e, name)
                raise
        else:
            with self._opener.open(meta["url"]) as f:
                try:
                    return fn(f, **fn_kwds)
                except Exception as e:
                    self._handle_pyarrow_date_error(e, name)
                    raise

    def url(
        self, name: Dataset | LiteralString, suffix: Extension | None = None, /
    ) -> str:
        frame = self._query(name, suffix)
        meta = next(_iter_metadata(frame))
        if is_parquet(meta.items()) and not is_available("vegafusion"):
            raise AltairDatasetsError.from_url(meta)
        url = meta["url"]
        if isinstance(url, str):
            return url
        else:
            msg = f"Expected 'str' but got {type(url).__name__!r}\nfrom {url!r}."
            raise TypeError(msg)

    # TODO: (Multiple)
    # - Settle on a better name
    # - Add method to `Loader`
    # - Move docs to `Loader.{new name}`
    def open_markdown(self, name: Dataset, /) -> None:
        """
        Learn more about a dataset, opening `vega-datasets/datapackage.md`_ with the default browser.

        Additional info *may* include: `description`_, `schema`_, `sources`_, `licenses`_.

        .. _vega-datasets/datapackage.md:
            https://github.com/vega/vega-datasets/blob/main/datapackage.md
        .. _description:
            https://datapackage.org/standard/data-resource/#description
        .. _schema:
            https://datapackage.org/standard/table-schema/#schema
        .. _sources:
            https://datapackage.org/standard/data-package/#sources
        .. _licenses:
            https://datapackage.org/standard/data-package/#licenses
        """
        import webbrowser

        from altair.utils import VERSIONS

        ref = self._query(name).get_column("file_name").item(0).replace(".", "")
        tag = VERSIONS["vega-datasets"]
        url = f"https://github.com/vega/vega-datasets/blob/v{tag}/datapackage.md#{ref}"
        webbrowser.open(url)

    @overload
    def profile(self, *, show: Literal[False] = ...) -> _SupportProfile: ...

    @overload
    def profile(self, *, show: Literal[True]) -> None: ...

    def profile(self, *, show: bool = False) -> _SupportProfile | None:
        """
        Describe which datasets can be loaded as tabular data.

        Parameters
        ----------
        show
            Print a densely formatted repr *instead of* returning a mapping.
        """
        relevant_columns = set(
            chain.from_iterable(impl._relevant_columns for impl in self._read)
        )
        frame = self._scan_metadata().select("dataset_name", *relevant_columns)
        inc_expr = nw.any_horizontal(impl._include_expr for impl in self._read)
        result: _SupportProfile = {
            "unsupported": _dataset_names(frame, ~inc_expr),
            "supported": _dataset_names(frame, inc_expr),
        }
        if show:
            import pprint

            pprint.pprint(result, compact=True, sort_dicts=False)
            return None
        return result

    def _query(
        self, name: Dataset | LiteralString, suffix: Extension | None = None, /
    ) -> nw.DataFrame[IntoDataFrameT]:
        """
        Query a tabular version of `vega-datasets/datapackage.json`_.

        Applies a filter, erroring out when no results would be returned.

        .. _vega-datasets/datapackage.json:
            https://github.com/vega/vega-datasets/blob/main/datapackage.json
        """
        constraints = _into_constraints(name, suffix)
        frame = self._scan_metadata(**constraints).collect()
        if not frame.is_empty():
            return frame
        else:
            msg = f"Found no results for:\n    {constraints!r}"
            raise ValueError(msg)

    def _merge_kwds(self, meta: Metadata, kwds: dict[str, Any], /) -> Mapping[str, Any]:
        """
        Extend user-provided arguments with dataset & library-specfic defaults.

        .. important:: User-provided arguments have a higher precedence.
        """
        if self._schema_cache.is_active() and (
            schema := self._schema_cache.schema_kwds(meta)
        ):
            kwds = schema | kwds if kwds else schema
        return kwds

    @property
    def _metadata_frame(self) -> nw.LazyFrame[IntoLazyFrameT]:
        fp = self._metadata_path
        return nw.from_native(self.scan_fn(fp)(fp)).lazy()

    def _scan_metadata(
        self, *predicates: OneOrSeq[IntoExpr], **constraints: Unpack[Metadata]
    ) -> nw.LazyFrame[IntoLazyFrameT]:
        if predicates or constraints:
            return self._metadata_frame.filter(*predicates, **constraints)
        return self._metadata_frame

    def _solve(
        self, meta: Metadata, impls: Sequence[BaseImpl[R]], /
    ) -> Callable[..., R]:
        """
        Return the first function that satisfies dataset constraints.

        See Also
        --------
        ``altair.datasets._readimpl.BaseImpl.unwrap_or_skip``
        """
        items = meta.items()
        it = (some for impl in impls if (some := impl.unwrap_or_skip(items)))
        if fn_or_err := next(it, None):
            if _is_err(fn_or_err):
                raise fn_or_err.from_tabular(meta, self._name)
            return fn_or_err
        raise AltairDatasetsError.from_tabular(meta, self._name)