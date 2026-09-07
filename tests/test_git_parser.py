import pytest
from ingestion.git_parser import GitHistoryParser


def test_parse_unified_diff():
    sample_diff = """diff --git a/account_service.py b/account_service.py
index abc1234..def5678 100644
--- a/account_service.py
+++ b/account_service.py
@@ -10,6 +10,8 @@ def create_account(customer_id):
     acc = {"id": customer_id}
+    acc["tier"] = "GOLD"
+    acc["kyc"] = True
     return acc
diff --git a/new_feature.py b/new_feature.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_feature.py
@@ -0,0 +1,5 @@
+def new_func():
+    return True
"""
    parser = GitHistoryParser()
    changes = parser.parse_unified_diff(sample_diff)

    assert len(changes) == 2
    c1 = changes[0]
    assert c1.file_path == "account_service.py"
    assert c1.change_type == "MODIFIED"
    assert len(c1.added_lines) == 2

    c2 = changes[1]
    assert c2.file_path == "new_feature.py"
    assert c2.change_type == "ADDED"
    assert len(c2.added_lines) >= 1


def test_parse_commit_log():
    sample_log = """commit a1b2c3d4e5f678901234567890abcdef12345678
Author: Jane Dev <jane@company.com>
Date:   Mon Sep 7 10:00:00 2026 +0000

    Add overdraft limit checking for REQ-004

diff --git a/transfer_service.py b/transfer_service.py
index 1111111..2222222 100644
--- a/transfer_service.py
+++ b/transfer_service.py
@@ -1,4 +1,5 @@
 def check_overdraft():
+    return True
"""
    parser = GitHistoryParser()
    commits = parser.parse_commit_log(sample_log)

    assert len(commits) == 1
    commit = commits[0]
    assert commit.commit_hash == "a1b2c3d4e5f678901234567890abcdef12345678"
    assert "Jane Dev" in commit.author
    assert "REQ-004" in commit.message
    assert len(commit.changes) == 1
    assert commit.changes[0].file_path == "transfer_service.py"
