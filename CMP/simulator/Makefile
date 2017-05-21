single_cycle:make.py
	python3 make.py
	rm -r dist build __pycache__
	rm CMP.spec

clean:
	rm CMP

cleanstd:
	rm snapshot_std.rpt

diff:
	diff snapshot.rpt snapshot_std.rpt -q
	diff report.rpt report_std.rpt -q
