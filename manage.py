import os
from app import create_app, db
from app.models import User, Role, CalBoard, StoreBoard, ControlBoard,\
                        Task
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.environ.get('FLASKY_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, CalBoard=CalBoard,
                StoreBoard=StoreBoard, ControlBoard=ControlBoard, Task=Task)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
