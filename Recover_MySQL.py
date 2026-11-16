"""Interactive administrator recovery for this laptop; never logs passwords.

Official procedure: https://dev.mysql.com/doc/refman/9.7/en/resetting-permissions.html
Only root@localhost is reset. A new, project-scoped account is created.
"""
from pathlib import Path
import ctypes, getpass, json, os, secrets, subprocess, tempfile, time
import urllib.request, http.cookiejar, re
import pymysql

ROOT=Path(__file__).resolve().parent
RESULT=ROOT/'.local'/'mysql_recovery_status.json'
MYSQLD=Path(r'C:\Program Files\MySQL\MySQL Server 9.7\bin\mysqld.exe')
CONFIG=Path(r'C:\ProgramData\MySQL\MySQL Server 9.7\my.ini')
SERVICE='MySQL97'

def status(state,**extra):
    RESULT.parent.mkdir(exist_ok=True)
    RESULT.write_text(json.dumps(dict(state=state,**extra),indent=2),encoding='utf-8')

def service(action):
    cmd=f"{action}-Service -Name '{SERVICE}' -ErrorAction Stop; (Get-Service '{SERVICE}').WaitForStatus('{ 'Stopped' if action=='Stop' else 'Running' }',[TimeSpan]::FromSeconds(45))"
    subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],check=True,capture_output=True)

def password(label):
    while True:
        first=getpass.getpass(label+': ')
        if len(first)<14 or any(c in first for c in '\r\n\x00'):
            print('Use at least 14 characters, with no line breaks.');continue
        if first!=getpass.getpass('Confirm '+label.lower()+': '):
            print('Passwords did not match. Try again.');continue
        return first

def wait_connect(user,pw,timeout=60):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:return pymysql.connect(host='127.0.0.1',port=3306,user=user,password=pw,autocommit=True,connect_timeout=2)
        except pymysql.MySQLError:time.sleep(1)
    raise RuntimeError('MySQL did not accept the new login within the allotted time.')

def app_connect(user,pw):
    jar=http.cookiejar.CookieJar()
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    html=client.open('http://127.0.0.1:8765/settings',timeout=10).read().decode()
    token=re.search(r'<meta name="csrf-token" content="([^"]+)"',html)
    if not token:raise RuntimeError('Application session token not found.')
    data=json.dumps(dict(host='127.0.0.1',port=3306,user=user,password=pw)).encode()
    req=urllib.request.Request('http://127.0.0.1:8765/api/database/mysql',data=data,headers={'Content-Type':'application/json','X-CSRF-Token':token[1]})
    result=json.load(client.open(req,timeout=60))
    if result.get('backend')!='MySQL':raise RuntimeError('Application did not confirm MySQL.')
    return client

def main():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError('Run the recovery launcher as administrator.')
    if not MYSQLD.is_file() or not CONFIG.is_file():
        raise RuntimeError('Expected MySQL 9.7 installation was not found. Nothing changed.')
    print('PlanFlow local MySQL recovery')
    print('This resets root@localhost and briefly restarts MySQL. Existing databases are retained.')
    print('Save the two passwords in your password manager. Do not send them in chat.')
    root_pw=password('New MySQL root password')
    app_pw=password('New PlanFlow database password')
    app_user='planflow_'+secrets.token_hex(3)
    status('passwords_entered',username=app_user)
    recovery=None;admin=None;stopped=False;temp=None
    try:
        # Restrict the recovery folder before writing any password-bearing SQL.
        temp=Path(tempfile.mkdtemp(prefix='PlanFlowMySQLRecovery_'))
        sid=subprocess.check_output(['whoami','/user','/fo','csv','/nh'],text=True).strip().split(',')[-1].strip('"')
        subprocess.run(['icacls.exe',str(temp),'/inheritance:r','/grant:r',f'*{sid}:(OI)(CI)F','*S-1-5-18:(OI)(CI)F'],check=True,capture_output=True)
        init=temp/'reset.sql'
        escaped=pymysql.converters.escape_string(root_pw)
        init.write_text("SET SESSION sql_mode = '';\nALTER USER 'root'@'localhost' IDENTIFIED BY '"+escaped+"';\n",encoding='utf-8')
        print('Stopping the MySQL service...')
        service('Stop');stopped=True
        status('recovering',username=app_user)
        with (temp/'startup.log').open('wb') as log:
            recovery=subprocess.Popen([str(MYSQLD),'--defaults-file='+str(CONFIG),'--init-file='+str(init),'--console'],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        admin=wait_connect('root',root_pw)
        init.unlink(missing_ok=True)
        with admin.cursor() as c:
            c.execute('CREATE DATABASE IF NOT EXISTS planflow_app_october_2026 CHARACTER SET utf8mb4')
            c.execute('CREATE USER %s@\'localhost\' IDENTIFIED BY %s',(app_user,app_pw))
            c.execute('GRANT ALL PRIVILEGES ON planflow_app_october_2026.* TO %s@\'localhost\'',(app_user,))
        print('New administrator password verified; project account created.')
        with admin.cursor() as c:c.execute('SHUTDOWN')
        admin.close();admin=None
        recovery.wait(timeout=60)
        service('Start');stopped=False
        verify=wait_connect(app_user,app_pw);verify.close()
        status('mysql_ready',username=app_user,host='127.0.0.1',port=3306)
        try:
            app_connect(app_user,app_pw)
            status('connected',username=app_user,host='127.0.0.1',port=3306,database='planflow_app_october_2026')
            print('PlanFlow is connected to MySQL.')
        except Exception:
            print('MySQL login works. Enter the details below on PlanFlow settings to connect.')
        print('PlanFlow username:',app_user)
        print('Host: 127.0.0.1   Port: 3306')
        print('Use the PlanFlow password you entered, and save this username.')
        print('The application currently keeps its connection in memory until it stops.')
    finally:
        if admin:
            try:
                with admin.cursor() as c:c.execute('SHUTDOWN')
            except Exception:pass
            admin.close()
        if recovery and recovery.poll() is None:
            try:recovery.wait(timeout=15)
            except subprocess.TimeoutExpired:
                print('Recovery server is still running. Do not start another MySQL instance.')
                status('attention_required',reason='Recovery server still running',pid=recovery.pid)
        if stopped and (not recovery or recovery.poll() is not None):
            try:service('Start')
            except Exception:print('MySQL service needs attention in Windows Services.')
        if temp:
            # Only files generated by this helper, never MySQL data files.
            for name in ('reset.sql','startup.log'):
                try:(temp/name).unlink(missing_ok=True)
                except OSError:pass
            try:temp.rmdir()
            except OSError:pass

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Recovery did not finish. Error type:',type(exc).__name__)
        # Exception messages can contain account information; never record passwords.
        if not RESULT.exists():status('failed',error_type=type(exc).__name__)
    finally:
        input('Press Enter to close this window...')
