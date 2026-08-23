def run_gpg(self, *args, **kw):
        if os.name != "posix":
            raise unittest.SkipTest("doesn't have gpg")

        command = (
            "gpg",
            "--batch",
            "--armor",
            "--homedir",
            self.ringdir,
            "--trust-model",
            "always",
        ) + args
        stdin = kw.pop("stdin", None)
        pipe = subprocess.Popen(
            command,
            shell=False,
            stdin=subprocess.PIPE if stdin else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = pipe.communicate(stdin)
        if pipe.returncode != 0:
            raise OSError(
                'Error running command "{}":\n{}\n'.format(
                    " ".join(command), err.decode("utf8")
                )
            )
        return out.decode("utf8"), err.decode("utf8")