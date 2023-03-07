"""
_*_ coding:utf-8 _*_
@Version  : 2.0.0
@Time     : 2023/03/07
@Author   : DuYu
@File     : ACS.py
@Describe : 软工(开发)21-1班数据库原理课程作业提交系统网站后端应用程序。
@Copyright:
            Copyright (c) 2022~2023 DuYu (No.202103180009), Faculty of Computer Science & Technology, Qilu University of Technology.
@Note     :
            1. 目前该程序只能在Python3.7中运行，flask框架对过高或过低版本的python都有不兼容的地方。
            2. 部署到Linux系统中运行时，警惕系统默认的字符编码，非UTF-8编码会导致处理所有的中文时失败或失效。
            3. v1.0版本的作业提交系统用于收集我班Web前端设计与开发课程的实验报告，目前该系统已弃用。
"""

import os
import sys
import time
import random
import base64
import zipfile
import sqlite3
import logging
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__, template_folder='./templates', static_folder='./static', static_url_path="/")
app.logger.setLevel(logging.DEBUG)
app.config['UPLOAD_FOLDER'] = os.path.join(sys.path[0], "collection/")
app.config['JSON_AS_ASCII'] = False
databasePath = os.path.join(sys.path[0], 'ACS_database.db')
ADMINISTRATOR_PASSWORD = "PASSWORD" # 管理员密码涉及到个人隐私，做保密处理。管理员密码在此处代码中“写死”，不可修改。
problemsSet = [
    {'id': 1, 'problem': '问题1', 'answer': '答案1'},
    {'id': 2, 'problem': '问题2', 'answer': '答案2'},
    {'id': 3, 'problem': '问题3', 'answer': '答案3'},
    # 问题涉及到个人隐私，做保密处理。
]


@app.route("/")
def root():
    return render_template('login.html')


@app.route("/getProblems", methods=['post'])
def getProblems():
    random.seed(time.time() * 9.0)
    problems = random.sample(problemsSet, k=3)
    return jsonify(
        {
            'problem01':
                {
                    'id': problems[0]['id'],
                    'problem': problems[0]['problem'],
                },
            'problem02':
                {
                    'id': problems[1]['id'],
                    'problem': problems[1]['problem'],
                },
            'problem03':
                {
                    'id': problems[2]['id'],
                    'problem': problems[2]['problem'],
                },
        }
    )


@app.route("/submit", methods=["get", "post"])
def submit():
    dic = request.get_json()
    name = dic['name']
    idnum = dic['id']
    password_enc = dic['password_enc']
    problem_01 = dic['problem_01']
    problem_01_id = dic['problem_01_id']
    problem_02 = dic['problem_02']
    problem_02_id = dic['problem_02_id']
    problem_03 = dic['problem_03']
    problem_03_id = dic['problem_03_id']

    app.logger.info(problemsSet[int(problem_01_id) - 1]['answer'])

    if problemsSet[int(problem_01_id) - 1]['answer'] != problem_01 or problemsSet[int(problem_02_id) - 1][
        'answer'] != problem_02 or problemsSet[int(problem_03_id) - 1]['answer'] != problem_03:
        return jsonify({
            'code': 1,
            'describe': '问题验证回答错误'
        })
    # namelistPath = os.path.join(sys.path[0], 'ACS_database.db')
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select * from namelist where id=" + str(idnum))
    rows = cursor.fetchall()
    if len(rows) != 0:
        conn.close()
        return jsonify({
            'code': 2,
            'describe': '该学号已被注册，如有问题请联系课代表。'
        })
    sql02 = "INSERT INTO namelist (id,name,password,reg_time) VALUES (" + ",".join(
        ["'" + idnum + "'", "'" + name + "'", "'" + password_enc + "'", "'" + str(time.time_ns()) + "'"]) + ")"
    cursor.execute(sql02)
    conn.commit()
    cursor.execute("select * from namelist where id=" + str(idnum))
    rows = cursor.fetchall()
    if len(rows) == 0:
        conn.close()
        return jsonify({
            'code': 3,
            'describe': '未知原因注册失败，请联系课代表。'
        })
    conn.close()
    return jsonify({
        'code': 0,
        'describe': ''
    })


@app.route("/login", methods=['post'])
def login():
    dic = request.get_json()
    idnum = dic['idnum']
    password_enc = dic['password_enc']
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select * from namelist where id=" + idnum)
    result = cursor.fetchall()
    if not result:
        conn.close()
        return jsonify({
            'code': 5,
            'describe': '该账号不存在，请检查输入的学号是否正确，或注册一个账号。'
        })
    password_enc_real = result[0][2]
    if password_enc_real != password_enc:
        conn.close()
        return jsonify({
            'code': 4,
            'describe': '密码错误'
        })

    conn.close()
    return jsonify({
        'code': 0,
        'describe': '',
        'idnum': result[0][0],
        'name': result[0][1]
    })


@app.route('/requireAssignment', methods=['post'])
def requireAssignment():
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select * from currentAssignment")
    result = cursor.fetchall()
    dicttemp02 = dict()
    number = 0
    for i in result:
        number = number + 1
        s = str(number) + '-Assignment'
        arrtemp = {
            'assid': i[0],
            'assignment': i[1],
            'startline': i[2],
            'deadline': i[3]
        }
        dicttemp02[s] = arrtemp
    conn.close()
    return jsonify(dicttemp02)


@app.route("/requireIsSubmitted", methods=["post"])
def requireIsSubmitted():
    dic = request.get_json()
    idnum = dic['idnum']
    assid = dic['assid']
    if assid == '-1':
        return jsonify({'submitState': -1})
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select * from submitState where idnum=" + idnum + ' and ' + "assignment_id=" + assid)
    result = cursor.fetchall()
    if result:
        return jsonify({'submitState': 1})  # Submitted
    else:
        return jsonify({'submitState': 0})  # Not submit


@app.route("/submitFile", methods=['POST'])
def submitFile():
    # dic = request.get_json()
    # idnum = dic['idnum']
    # assid = dic['assid']
    # name = dic['name']
    idnum = request.form.get('idnum')
    assid = request.form.get('assid')
    name = request.form.get('name')
    sub_time = str(int(time.time() * 1000))  # Unit = ms
    if assid == '-1':
        return jsonify({
            'submitState': -1,
            'describe': '请您首先选择作业项。'
        })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select * from submitState where idnum=" + idnum + ' and ' + "assignment_id=" + assid)
    result = cursor.fetchall()
    if result:
        conn.close()
        return jsonify({
            'submitState': 1,
            'describe': '您已经提交了作业，不可重复提交。',
        })
    else:
        # Receive File and change database
        f = request.files['assignmentFile']
        extName = os.path.splitext(secure_filename(f.filename))[1]
        fileSaveName = '作业' + str(assid) + '-软工(开发)21-1' + str(name) + "-" + sub_time + extName
        fileSavePathName = os.path.join(app.config['UPLOAD_FOLDER'], fileSaveName)
        f.save(fileSavePathName)
        if not os.path.exists(fileSavePathName):
            return jsonify({
                'submitState': 2,
                'describe': '您中断了文件的上传',
            })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select value from id_counter where name='submit_id'")
    result = cursor.fetchall()
    sbid = int(result[0][0])
    cursor = conn.cursor()
    cursor.execute("update id_counter set value=" + str(sbid + 1) + " where name='submit_id'")
    conn.commit()
    conn.close()

    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("insert into submitState values (" + ",".join(
        ["'" + str(sbid + 1) + "'", "'" + str(idnum) + "'", "'" + str(name) + "'", "'" + str(assid) + "'",
         "'" + str(fileSaveName) + "'", "'" + str(sub_time) + "'"]) + ")")
    conn.commit()
    conn.close()

    return jsonify({
        'submitState': 0,
        'describe': '',
    })


@app.route("/deleteFile", methods=['POST'])
def deleteFile():
    dic = request.get_json()
    idnum = dic['idnum']
    assid = dic['assid']
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select filename from submitState where idnum=" + str(idnum) + " and assignment_id=" + str(assid))
    result = cursor.fetchall()
    cursor.execute("delete from submitState where idnum=" + str(idnum) + " and assignment_id=" + str(assid))
    conn.commit()
    fn = result[0][0]
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], fn))
    except Exception:
        pass
    return jsonify({
        'code': 0,
        'describe': '',
    })


@app.route('/requireAllPeople', methods=['post'])
def requireAllPeople():
    dic = request.get_json()
    admin_password = dic['admin_password']
    if admin_password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '授权错误，您不能非法调用该API进行相关操作。',
        })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select * from namelist")
    result = cursor.fetchall()
    return_dic = {'code': 0}
    re_data = {}
    number = 0
    for i in result:
        temp01 = str(i[2]).encode('ascii')
        temp02 = base64.b64decode(temp01)
        temp03 = temp02.decode('ascii')
        re_data['number' + str(number)] = {
            'idnum': i[0],
            'name': i[1],
            'password': i[2],
            'regtime': i[3]
        }
        number = number + 1
    return_dic['return_data'] = re_data
    return jsonify(return_dic)


@app.route("/deletePeople", methods=['post'])
def deletePeople():
    dic = request.get_json()
    idnum = dic['idnum']
    name = dic['name']
    password = dic['password']
    if password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '您输入的管理员密码错误'
        })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("delete from namelist where id=" + "'" + idnum + "'" + " and name=" + "'" + name + "'")
    conn.commit()
    conn.close()
    return jsonify({
        'code': 0,
        'describe': ''
    })
    pass


@app.route("/requireAllAssignment", methods=['post'])
def requireAllAssignment():
    dic = request.get_json()
    admin_password = dic['admin_password']
    if admin_password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '授权错误，您不能非法调用该API进行相关操作。',
        })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select * from currentAssignment")
    result = cursor.fetchall()
    return_dic = {'code': 0}
    re_data = {}
    number = 0
    for i in result:
        re_data['number' + str(number)] = {
            'assid': i[0],
            'assignment': i[1],
            'startline': i[2],
            'deadline': i[3]
        }
        number = number + 1
    return_dic['return_data'] = re_data
    return jsonify(return_dic)


@app.route("/deleteAssignment", methods=['post'])
def deleteAssignment():
    dic = request.get_json()
    assid = dic['assid']
    password = dic['password']
    if password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '您输入的管理员密码错误'
        })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("delete from currentAssignment where id=" + "'" + assid + "'")
    conn.commit()
    conn.close()
    return jsonify({
        'code': 0,
        'describe': ''
    })
    pass


@app.route("/deployAssignment", methods=['post'])
def deployAssignment():
    dic = request.get_json()
    aname = dic['aname']
    deadl = dic['deadl']
    password = dic['password']
    if password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '您输入的管理员密码错误'
        })
    startl_num = time.time_ns()
    deadl_num = int(deadl) * 1000000

    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select value from id_counter where name='assignment_id'")
    result = cursor.fetchall()
    sbid = int(result[0][0])
    cursor = conn.cursor()
    cursor.execute("update id_counter set value=" + str(sbid + 1) + " where name='assignment_id'")
    conn.commit()
    conn.close()

    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("insert into currentAssignment values (" + ",".join(
        ["'" + str(sbid + 1) + "'", "'" + str(aname) + "'", "'" + str(startl_num) + "'",
         "'" + str(deadl_num) + "'"]) + ")")
    conn.commit()
    conn.close()
    return jsonify({
        'code': 0,
        'describe': ''
    })
    pass


@app.route("/requireAllSubmitState", methods=['post'])
def requireAllSubmitState():
    dic = request.get_json()
    admin_password = dic['admin_password']
    if admin_password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '授权错误，您不能非法调用该API进行相关操作。',
        })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select * from submitState")
    result = cursor.fetchall()
    return_dic = {'code': 0}
    re_data = {}
    number = 0
    for i in result:
        re_data['number' + str(number)] = {
            'submitId': i[0],
            'idnum': i[1],
            'name': i[2],
            'assignmentId': i[3],
            'submitTime': i[5],
        }
        number = number + 1
    return_dic['return_data'] = re_data
    return jsonify(return_dic)


@app.route("/deleteAllF", methods=['post'])
def deleteAllF():
    dic = request.get_json()
    assid = dic['assid']
    password = dic['password']
    if password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '您输入的管理员密码错误'
        })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select filename from submitState where assignment_id=" + "'" + assid + "'")
    result = cursor.fetchall()
    cursor.execute("delete from submitState where assignment_id=" + "'" + assid + "'")
    conn.commit()
    conn.close()
    for i02 in result:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], i02[0]))
        except Exception:
            pass
    return jsonify({
        'code': 0,
        'describe': ''
    })
    pass


@app.route("/downloadOneFile", methods=['get'])
def downloadOneFile():
    submit_id = request.args.get('subid')
    password = request.args.get('password')
    if password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '您输入的管理员密码错误'
        })
    conn = sqlite3.connect(database=databasePath)
    cursor = conn.cursor()
    cursor.execute("select filename from submitState where submit_id=" + "'" + submit_id + "'")
    result = cursor.fetchall()
    conn.close()
    if not result:
        return jsonify({
            'code': 2,
            'describe': '文件不存在。'
        })
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], result[0][0]), as_attachment=True)
    pass


@app.route("/downloadAllFile", methods=['get'])
def downloadAllFile():
    password = request.args.get('password')
    if password != ADMINISTRATOR_PASSWORD:
        return jsonify({
            'code': 1,
            'describe': '您输入的管理员密码错误'
        })
    with zipfile.ZipFile(os.path.join(sys.path[0], "assignments.zip"), 'w', zipfile.ZIP_DEFLATED,
                         allowZip64=True) as myzip:
        arr = os.listdir(app.config['UPLOAD_FOLDER'])
        for i03 in arr:
            myzip.write(os.path.join(app.config['UPLOAD_FOLDER'], i03), "\\" + i03, zipfile.ZIP_DEFLATED)
    return send_file(os.path.join(sys.path[0], "assignments.zip"), as_attachment=True)
    pass


@app.route('/isAdmin', methods=['post'])
def isAdmin():
    dic = request.get_json()
    password = dic['password']
    if password==ADMINISTRATOR_PASSWORD:
        return jsonify({'code':0})
    else:
        return jsonify({'code':1})


if __name__ == '__main__':
    app.run(debug=False, port=80,host='0.0.0.0')
