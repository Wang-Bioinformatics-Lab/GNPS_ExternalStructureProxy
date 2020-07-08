from app import app

import json
import csv
import requests
import os
import uuid

from flask import abort, jsonify, render_template, request, redirect, url_for, send_file, send_from_directory
from ftplib import FTP
import werkzeug

@app.route('/massiveftpproxy', methods=['GET'])
def proxy_massive_file():
    ftppath = request.args.get("ftppath")

    # Normalizing Path
    ftppath = ftppath.replace("ftp://", "")
    ftppath = ftppath.replace("massive.ucsd.edu", "")
    if ftppath[0] != "/":
        ftppath = "/" + ftppath

    # Passing through file
    ftp = FTP('massive.ucsd.edu')
    ftp.login()
    secure_filename = os.path.basename(werkzeug.utils.secure_filename(ftppath))
    local_filename = os.path.join("/ftpproxy", secure_filename)
    # Writing file
    ftp.retrbinary('RETR '+ ftppath, open(local_filename, 'wb').write)
    ftp.quit()

    file_handle = open(local_filename, 'r')

    # This *replaces* the `remove_file` + @after_this_request code above
    def stream_and_remove_file():
        yield from file_handle
        file_handle.close()
        os.remove(local_filename)

    return app.response_class(
        stream_and_remove_file(),
        headers={'Content-Disposition': 'attachment', 'filename': secure_filename}
    )