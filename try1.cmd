call conda activate base
del invest_cmd.log
del err.log
del invest.db
echo %time%
python invest.py 1>invest_cmd.log 2>err.log
echo %time%
pause
