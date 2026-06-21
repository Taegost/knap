Run /ce-work $ARGUMENTS. When it finishes, run /knap-verify-implementation. If /knap-verify-implementation reports PARTIAL or FAIL, run /ce-work $ARGUMENTS again to address them, then run /knap-verify-implementation again. Continue this cycle until /knap-verify-implementation reports PASS.

When verification passes, do the following:
1. Update the plan file's frontmatter `status` field from `active` to `completed`.
2. Run `/ce-compound Full, No Session History`.
3. Commit and push. 
4. Summarize what was done.