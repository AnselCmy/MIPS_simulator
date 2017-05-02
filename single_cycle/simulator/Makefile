single_cycle:make.py
	python3 make.py
	rm -r dist build __pycache__
	rm single_cycle.spec

clean:
	rm single_cycle

cleanrpt:
	rm snapshot_std.rpt
	rm error_dump_std.rpt

diff:
	diff snapshot.rpt snapshot_std.rpt
	diff error_dump.rpt error_dump_std.rpt