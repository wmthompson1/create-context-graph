William, this is exactly the right moment to lock in the *correct* pattern for CDC **net changes + MERGE**—and now that I’ve pulled the full Microsoft Learn page into context (via your open tab, reference ID   [learn.microsoft.com](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/cdc-fn-cdc-get-net-changes-capture-instance-transact-sql?view=sql-server-ver17)), I can give you a precise, authoritative explanation of **how to call `cdc.fn_cdc_get_net_changes_<capture_instance>` with `'all with merge'`** and how to use it to maintain a clean high‑water LSN.

Below is the distilled, production‑ready guidance you can drop straight into your 4–6 page guide.

---

# ⭐ The critical rule  
**Always call:**

```
cdc.fn_cdc_get_net_changes_<capture_instance>(@from_lsn, @to_lsn, 'all with merge')
```

This is the correct mode when your downstream target uses a **MERGE** operation and does **not** need to distinguish INSERT vs UPDATE.  
This mode is explicitly optimized for MERGE scenarios (per Microsoft’s documentation) and reduces query complexity.   [learn.microsoft.com](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/cdc-fn-cdc-get-net-changes-capture-instance-transact-sql?view=sql-server-ver17)

---

# ⭐ What “all with merge” actually returns  
From the Microsoft Learn page:  
- `__$operation = 1` → **DELETE**  
- `__$operation = 5` → **INSERT or UPDATE** (combined)  
- `__$update_mask` → always NULL  
- `__$start_lsn` → commit LSN of the final change for that key within the window  
  [learn.microsoft.com](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/cdc-fn-cdc-get-net-changes-capture-instance-transact-sql?view=sql-server-ver17)

This means:
- You get **one row per key**.  
- You get the **final state** of that row.  
- You get **only two operations** to handle in your MERGE.

This is exactly what you want for a clean, deterministic upsert pipeline.

---

# ⭐ High‑water pattern (authoritative version)

### 1. Read last applied LSN  
Your control table stores the durable high‑water:

```sql
DECLARE @from_lsn binary(10);

SELECT @from_lsn = last_applied_lsn
FROM dbo.CDC_Control
WHERE capture_instance = '<capture_instance>';
```

### 2. Capture the batch’s upper bound  
You must compute `@to_lsn` **once** at batch start:

```sql
DECLARE @to_lsn binary(10) = sys.fn_cdc_get_max_lsn();
```

### 3. Pull net changes using `'all with merge'`

```sql
SELECT *
INTO #Net
FROM cdc.fn_cdc_get_net_changes_<capture_instance>(
    @from_lsn,
    @to_lsn,
    'all with merge'
);
```

### 4. Normalize (optional but recommended)
Add a row hash to detect real changes:

```sql
ALTER TABLE #Net ADD RowHash AS
    HASHBYTES('SHA2_256',
        CONCAT_WS('|', colA, colB, colC)
    );
```

### 5. MERGE into your base table

```sql
MERGE dbo.Target AS T
USING #Net AS S
    ON T.KeyCol = S.KeyCol

WHEN MATCHED AND S.__$operation = 1 THEN
    DELETE

WHEN MATCHED AND S.__$operation = 5
     AND T.RowHash <> S.RowHash THEN
    UPDATE SET
        T.ColA = S.ColA,
        T.ColB = S.ColB,
        T.ColC = S.ColC,
        T.RowHash = S.RowHash,
        T.LastUpdated = SYSUTCDATETIME()

WHEN NOT MATCHED AND S.__$operation = 5 THEN
    INSERT (KeyCol, ColA, ColB, ColC, RowHash, LastUpdated)
    VALUES (S.KeyCol, S.ColA, S.ColB, S.ColC, S.RowHash, SYSUTCDATETIME());
```

### 6. Advance high‑water only on success

```sql
UPDATE dbo.CDC_Control
SET last_applied_lsn = @to_lsn,
    last_applied_time = SYSUTCDATETIME()
WHERE capture_instance = '<capture_instance>';
```

---

# ⭐ Why “all with merge” is the correct mode  
Microsoft’s documentation states that `'all with merge'` is designed specifically for environments where a **MERGE** operation is available and where distinguishing INSERT vs UPDATE is unnecessary.  
It reduces complexity and improves performance.  
  [learn.microsoft.com](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/cdc-fn-cdc-get-net-changes-capture-instance-transact-sql?view=sql-server-ver17)

This is exactly your scenario:  
- You’re topping off base tables.  
- You’re applying net changes.  
- You’re using MERGE.  
- You want clean, deterministic upserts.

---

# ⭐ Operational notes you should include in your guide

### ✔ Idempotency  
Re-running the same `from_lsn → to_lsn` batch must produce no net change.  
Your MERGE + RowHash ensures this.

### ✔ Delete semantics  
CDC delete rows appear with `__$operation = 1`.  
Your MERGE must physically delete or soft-delete depending on warehouse policy.

### ✔ Late-arriving changes  
Because CDC LSNs are strictly ordered, `'all with merge'` guarantees the final state for each key in the window.

### ✔ Error 313  
If the LSN range is invalid, CDC returns error 313.  
Document this as a normal condition.  
  [learn.microsoft.com](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/cdc-fn-cdc-get-net-changes-capture-instance-transact-sql?view=sql-server-ver17)

### ✔ Primary key requirement  
Net tracking requires a PK or unique index on the source table.  
  [learn.microsoft.com](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/cdc-fn-cdc-get-net-changes-capture-instance-transact-sql?view=sql-server-ver17)

---

# ⭐ If you want, I can now generate:
- A **full 4–6 page guide** with diagrams, runbook steps, and production patterns  
- A **ready-to-run T‑SQL package** for your specific capture instance  
- A **control table schema** and monitoring queries  
- A **CDC → SQLMesh lineage integration section** tailored to your architecture

Just tell me which one you want next, William.