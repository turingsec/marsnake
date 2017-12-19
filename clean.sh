find ./ -name "*.pyc" -exec rm -f {} \;
find ./ -name "*.pyo" -exec rm -f {} \;
#find ./ -name "*.obj" -exec rm -f {} \;

if [ -f "lextab.py" ]; then
	rm lextab.py
fi

if [ -f "yacctab.py" ]; then
	rm yacctab.py
fi