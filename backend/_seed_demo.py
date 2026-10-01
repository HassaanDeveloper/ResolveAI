import re

from app.services.database import get_supabase_client

client = get_supabase_client()

sql = open("seeds/seed_all.sql", encoding="utf-8").read()
sql = re.sub(r"^\s*--.*$", "", sql, flags=re.M)


def segment(start_marker, end_marker):
    start = sql.index(start_marker)
    end = sql.index(end_marker, start)
    return sql[start:end]


def split_rows(seg):
    values_at = seg.index("VALUES")
    body = seg[values_at + len("VALUES"):]
    return re.findall(r"\(((?:[^()]|\([^()]*\))*)\)", body)


def split_fields(s):
    fields, cur, inq, depth, i = [], "", False, 0, 0
    while i < len(s):
        ch = s[i]
        if inq:
            if ch == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    cur += "''"
                    i += 2
                    continue
                inq = False
            cur += ch
        else:
            if ch == "'":
                inq = True
                cur += ch
            elif ch == "(":
                depth += 1
                cur += ch
            elif ch == ")":
                depth -= 1
                cur += ch
            elif ch == "," and depth == 0:
                fields.append(cur.strip())
                cur = ""
            else:
                cur += ch
        i += 1
    if cur.strip():
        fields.append(cur.strip())
    return fields


def val(v, cust_map, order_map):
    v = v.strip()
    if v.upper() == "NULL":
        return None
    m = re.fullmatch(r"\(SELECT id FROM customers WHERE external_customer_id = '([^']+)'\)", v)
    if m:
        return cust_map[m.group(1)]
    m = re.fullmatch(r"\(SELECT id FROM orders WHERE order_number = '([^']+)'\)", v)
    if m:
        return order_map[m.group(1)]
    m = re.fullmatch(r"'(.*?)'::(date|timestamptz)", v, re.S)
    if m:
        return m.group(1).replace(" ", "T", 1) if m.group(2) == "timestamptz" else m.group(1)
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1].replace("''", "'")
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def insert_missing(table, rows, key_col, out_keys=None):
    existing = {r[key_col] for r in client.table(table).select(key_col).execute().data}
    missing = [r for r in rows if r[key_col] not in existing]
    if missing:
        client.table(table).insert(missing).execute()
    if out_keys is not None:
        out_keys.update(r[key_col] for r in missing)
    print(f"{table}: parsed={len(rows)} existing={len(rows) - len(missing)} inserted={len(missing)}")
    return existing | {r[key_col] for r in missing}


# customers
cust_rows = [
    {f: val(v, {}, {}) for f, v in zip(
        ["external_customer_id", "name", "email", "account_status"], split_fields(r))}
    for r in split_rows(segment("INSERT INTO customers", "ON CONFLICT (external_customer_id)"))
]
insert_missing("customers", cust_rows, "external_customer_id")

cust_map = {r["external_customer_id"]: r["id"] for r in client.table("customers").select("id,external_customer_id").execute().data}

# orders
order_rows = [
    {f: val(v, cust_map, {}) for f, v in zip(
        ["order_number", "customer_id", "status", "total_amount", "currency"], split_fields(r))}
    for r in split_rows(segment("INSERT INTO orders", "ON CONFLICT (order_number)"))
]
insert_missing("orders", order_rows, "order_number")

order_map = {r["order_number"]: r["id"] for r in client.table("orders").select("id,order_number").execute().data}

# shipments (CTE: VALUES tuples -> columns of s(...))
ship_seg = segment("(VALUES", ") AS s(order_number")
ship_rows = [
    {"order_id": order_map.get(o), **{f: val(v, cust_map, order_map) for f, v in zip(
        ["carrier", "tracking_number", "status", "estimated_delivery_date", "delivered_at"], split_fields(r)[1:])}}
    for r in re.findall(r"\(((?:[^()]|\([^()]*\))*)\)", ship_seg.split("VALUES", 1)[1])
    for o in [split_fields(r)[0].strip("'")]
    if order_map.get(o)
]
insert_missing("shipments", ship_rows, "tracking_number")

# refunds
refund_rows = [
    {f: val(v, cust_map, order_map) for f, v in zip(
        ["order_id", "amount", "currency", "status", "operation_id", "processed_at"], split_fields(r))}
    for r in split_rows(segment("INSERT INTO refunds", "ON CONFLICT (operation_id)"))
]
insert_missing("refunds", refund_rows, "operation_id")

print("CUST-001:", client.table("customers").select("id").eq("external_customer_id", "CUST-001").execute().data)
print("10482:", client.table("orders").select("id,status").eq("order_number", "10482").execute().data)
