from deltalake import DeltaTable

dt = DeltaTable("data/denuncias")

table = dt.to_pyarrow_table()

for batch in table.to_batches():
    for row in batch.to_pylist():
        print(row)