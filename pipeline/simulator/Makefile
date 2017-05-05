single_cycle:make.py
	python3 make.py
	rm -r dist build __pycache__
	rm pipeline.spec

clean:
	rm pipeline

cleanstd:
	rm snapshot_std.rpt
	rm error_dump_std.rpt

diff:
	diff snapshot.rpt snapshot_std.rpt -q
	diff error_dump.rpt error_dump_std.rpt -q