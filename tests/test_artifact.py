from reonic import artifact


def test_signature_changes_with_the_data(tmp_path):
    (tmp_path / "a.csv").write_text("x\n1\n")
    s1 = artifact.signature(tmp_path)
    assert artifact.signature(tmp_path) == s1
    (tmp_path / "a.csv").write_text("x\n1\n2\n")
    assert artifact.signature(tmp_path) != s1


def test_saved_object_is_used_only_when_the_signature_matches(tmp_path):
    path = tmp_path / "m.joblib"
    assert artifact.load_if_fresh(path, "abc") is None  # nothing saved yet
    assert artifact.save(path, {"answer": 42}, "abc")
    assert artifact.load_if_fresh(path, "abc") == {"answer": 42}
    assert artifact.load_if_fresh(path, "different") is None  # code or data changed: rebuild


def test_unreadable_or_old_format_files_mean_rebuild(tmp_path):
    path = tmp_path / "m.joblib"
    path.write_bytes(b"not a pickle")
    assert artifact.load_if_fresh(path, "abc") is None
    import joblib
    joblib.dump(object(), path)  # an old file saved without a signature
    assert artifact.load_if_fresh(path, "abc") is None


def test_save_on_a_read_only_location_does_not_raise(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    assert artifact.save(blocker / "sub" / "m.joblib", 1, "s") is False
