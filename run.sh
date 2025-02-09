FLAGFILE_INSTALL="venv/.completed_installation"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

if [ ! -f $FLAGFILE_INSTALL ]; then
    venv/bin/python3 -m pip install --upgrade pip
    venv/bin/python3 -m pip install -U -r requirements.txt
    touch $FLAGFILE_INSTALL
fi

if [ -z "$(tmux list-sessions | grep $TMUX_SESSION)" ]; then
    venv/bin/python3 ./invoice_generator.py
fi
