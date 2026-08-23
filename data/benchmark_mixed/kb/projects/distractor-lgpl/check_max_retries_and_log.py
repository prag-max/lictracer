def check_max_retries_and_log(current_retries: int, exception_info: str = "") -> bool:
        """Check if max retries reached and log accordingly.

        Args:
            current_retries: The current retry count.
            exception_info: Additional context about the exception (e.g., "Timed out: ...").

        Returns:
            bool: True if max retries reached (should abort), False otherwise (should retry).
        """
        prefix_with_info = f"{log_prefix} {exception_info}" if exception_info else log_prefix

        if max_retries < 0 or current_retries < max_retries:
            _LOGGER.debug(
                "%s Failed run number %s of %s. Retrying.",
                prefix_with_info,
                current_retries,
                max_retries,
            )
            return False
        _LOGGER.exception(
            "%s Failed run number %s of %s. Aborting.",
            prefix_with_info,
            current_retries,
            max_retries,
        )
        return True