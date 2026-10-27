# Known issues

- `tests/test_zlog_server.py` `test_no_access` assumes writing to `/` fails with EACCES (Errno 13), but a read-only root, such as macOS's, gives EROFS (Errno 30), so the test fails there.
