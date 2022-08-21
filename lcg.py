# IMPORTANT!!!!
# to shut down the app, press Ctrl+C
# do not try to download more than 500 MB of files, the estimate will be shown in the app
# if you want to generate numbers with more than 100 digits, you have to change this variable to a prime number which has bigger value than number of demanded digits
digits = 97
# don't be too impatient to click the buttons, wait till the buttons are blue, or the app may bug out


from dash import Dash, dcc, html, Input, Output, State, ctx
import random
from decimal import *
import pandas as pd
import base64
import io
import csv 
from math import gcd
import sys
import webbrowser
from threading import Timer
sys.setrecursionlimit(1000000)
# optimizes the Decimal to be more precise
getcontext().prec = 60

# suppressing unwanted messages from console
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


boolean_for_message = False
just_used_button = False
# linear congruential generator (it´s a generator in Python as well)
# a: multiplicator, c: increment, m: modulus
def lcg(x, a, c, m):
    while True:
        x = (a * x + c) % m
        yield x

# function for determining the a, c, m numbers and convert the generated numbers so they fit in the selected bounds
def do_lcg(n, lower, upper, seed = random.randint(0, 2 ** digits)):
    a, c, m = 1103515245, 12345, 2 ** digits
    generator = lcg(seed, a, c, m)
    numbers = []

    for i in range(n):
        nextnumber = ((upper - lower) * next(generator)) // m + lower
        numbers.append(nextnumber)
    return numbers


# (NOT USED, for testing purposes)
# make a dictionary, where keys are the generated numbers and values are the counts of that numbers
def make_a_dictionary(list, count, lower, upper):
    dictionary = {}
    for i in range(count):
        if list[i] in dictionary:
            dictionary[list[i]] += 1
        else:
            dictionary[list[i]] = 1
    
    return dictionary

# Miller-Rabin test, n is the tested number, k the number of tests to be executed 
def miller_rabin(n, k = 40):
    
    # if the tested number is 2, it is automatically prime 
    if n == 2:
        return True
    
    if n == 3:
        return True

    # if the tested number is even, but not 2, it is clearly not a prime
    if n % 2 == 0:
        return False

    # decompose the number n-1 into 2**r and s
    r, s = 0, n - 1
    while s % 2 == 0:
        r += 1
        s //= 2

    # tests if n is prime for potentially k times
    for _ in range(k):
        # chooses random base a every time so the probability of getting a correct result increases with number of tests
        a = random.randrange(2, n - 1)
        x = pow(a, s, n)
        if x == 1 or x == n - 1:
            # is then prime according to this iteration of a test, so let's it repeat the loop to be sure
            continue
        for _ in range(r - 1):
            x = pow(a, 2, n)
            # is then prime according to this iteration of a test, so let's it repeat the loop to be sure
            if x == n - 1:
                break
        # if it didn't find a clue of it being a prime above, then it is 100% a composite number
        else:
            return False
    # after k > 40 successful attempts it is very probably a prime
    return True

# runs Miller-Rabin test on a list and returns a list of primes
def do_miller_test(list):
    result = []
    for x in list:
        if miller_rabin(x):
            result.append(x)
    return result

# unloads a csv file into a list
def parse_contents(contents):
    parsed = []
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string).decode('utf-8')
    with io.StringIO(decoded) as fp:
        reader = csv.reader(fp, delimiter=',', skipinitialspace=True)
        for row in reader:
            for b in row:
                parsed.append(b)
    return parsed

# Euclidian algorithm
def egcd(a: int, b: int):
    if a == 0:
        return (b, 0, 1)
    else:
        b_div_a, b_mod_a = divmod(b, a)
        g, x, y = egcd(b_mod_a, a)
        return (g, y - b_div_a * x, x)

def modinv(a: int, b: int) -> int:
    g, x, _ = egcd(a, b)
    return x % b

# when the text is converted into bytes, the integer is then calculated from that
# more here: https://stackoverflow.com/questions/50509017/how-is-int-from-bytes-calculated
# the integer must be smaller than the product of primes p, q
def countbytes(n):
    i = 1
    while True:
        if pow(256, i) >= n:
            return i - 1
        i += 1

# for estimating the size of file based on the lenght of numbers stored and their count
def estimate_size(lenght, count):
    # Adding two because its the lenght of text + comma + extra byte which translates to end of string
    size = (len(lenght) + 2) * count
    if len(str(size)) >= 7:
        return 'Estimated size: ' + str(size // 1048576) + ' MB'
    elif len(str(size)) >= 4:
        return 'Estimated size: ' + str(size // 1024) + ' kB'
    else:
        return 'Estimated size: ' + str(size) + ' B'

# defines the Dash app
app = Dash(__name__)

# Dash app layout, makes the user interface using html and css
# Dash has HTML components (e.g. html.Div) and Core components (e.g. dcc.Dropdown)
# list of HTML components here: https://dash.plotly.com/dash-html-components
# list of Core components here: https://dash.plotly.com/dash-core-components
# assigns components their unique id so they can be called later using Dash callbacks

app.layout = html.Div([
    html.Br(),
    html.Br(),

    #LCG
    html.H1('LCG'),
    html.Hr(style = {'width': '30%', 'margin-top': '0%', 'margin-bottom': '2%', 'border-top': '1.5px solid black', 'text-align': 'left', 'margin-left': '0'}),
    html.Div([
        html.Div([
            html.Div([
                html.Label('Count', style = {'width': '20%'}),
                dcc.Input(
                    id = 'count',
                    type = 'number',
                    placeholder = 'How many numbers to generate?',
                    style = {'display': 'inline-block', 'width': '60%'}
                )
            ], style = {'display': 'flex', 'margin-bottom': '2%'}),
            html.Div([
                html.Label('Boundaries', style = {'width': '20%'}),
                dcc.Input(
                    id = 'lower',
                    placeholder = 'Lower',
                    style = {'display': 'inline-block', 'width': '29%', 'margin-right': '2%'}
                ),
                dcc.Input(
                    id = 'upper',
                    placeholder = 'Upper',
                    style = {'display': 'inline-block', 'width': '29%'}
                )
            ], style = {'display': 'flex'})
        ], style = {'display': 'inline-block', 'width': '40%'}),
        html.Div([
            html.Div([
                html.Label('CSV', style = {'width': '15%'}),
                html.Div([
                    html.Button('Download CSV', id='btn_csv'),
                    dcc.Download(id='download-csv'),
                ])
            ], style = {'display': 'flex', 'margin-bottom': '2%'}),
            html.Div([
                html.Label('TXT', style = {'width': '15%'}),
                html.Div([
                    html.Button('Download TXT', id='btn_txt'),
                    dcc.Download(id='download-txt')
                ])
            ], style = {'display': 'flex',})
        ], style = {'display': 'inline-block', 'width': '40%'}),
        html.Br(),
        html.Br(),
        html.Div([
            html.Button('Generate', id='generate', style = {'display': 'inline-block', 'margin-left': '1%', 'margin-right': '1%'})
        ]),
 
        html.Div([''], id = 'estimated_size', style = {'margin-left': '1%', 'margin-top': '1%'}),
        dcc.Store(id = 'memory_lcg'),
    ], id = 'lcg'),
    dcc.Loading(id = 'loading_lcg', type = 'default', children = html.Div(id = 'loading_lcg_output')),
    dcc.Loading(id = 'loading_odd', type = 'default', children = html.Div(id = 'loading_odd_output')),
    html.Br(),
    html.Br(),

    # Miller-Rabin test
    html.H1('Miller-Rabin test'),
    html.Hr(style = {'width': '30%', 'margin-top': '0%', 'margin-bottom': '2%', 'border-top': '1.5px solid black', 'text-align': 'left', 'margin-left': '0'}),
    html.Div([
        html.Div([ 
            html.Div([
                html.Label('Action', style = {'width': '20%'}),
                dcc.Dropdown(
                    options = ['LCG', 'Upload'],
                    id = 'lcg_upload',
                    value = 'LCG',
                    searchable = False,
                    style = {'display': 'inline-block', 'width': '80%', 'margin-left': '0.5%'}
                ),
            ], style = {'display': 'flex'})
        ], style = {'display': 'inline-block', 'width': '40%'}),
        html.Div([

        ], style = {'display': 'inline-block', 'width': '40%'}),
    ], id = 'middle'),

    html.Div([
        html.Br(),
        html.Div([
            html.Div([
                html.Label('Optimalize', style = {'width': '20%'}),
                html.Button('Delete even numbers', id='odd_numbers', style = {'display': 'inline-block', 'margin-bottom': '2%'})
            ], style = {'display': 'flex'}),
            html.Div([
                html.Label('Upload', style = {'width': '20%'}),
                dcc.Upload(
                    id='upload_csv',
                    children = html.Div(['Upload ', html.A('csv. file')], style = {'display': 'inline-block'}),
                    style={
                        'width': '180%',
                        'lineHeight': '36px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'display': 'inline-block',
                        'margin-bottom': '6px'
                        }),
                html.Button('Remove', id='remove-button', n_clicks=0, style={'margin-left': '20%'}),
                dcc.Store(id = 'memory_csv')
            ], style = {'display': 'flex'})
        ], style = {'display': 'inline-block', 'width': '40%'}),
        html.Div([
            html.Div([
                html.Label('CSV', style = {'width': '15%'}),
                html.Div([
                    html.Button('Download CSV', id='btn_csv_rm'),
                    dcc.Download(id='download_csv_rm'),
                ])
            ], style = {'display': 'flex', 'margin-bottom': '2%'}),
            html.Div([
                html.Label('TXT', style = {'width': '15%'}),
                html.Div([
                    html.Button('Download TXT', id='btn_txt_rm'),
                    dcc.Download(id='download_txt_rm')
                ])
            ], style = {'display': 'flex',})
        ], style = {'display': 'inline-block', 'width': '40%'}),
        html.Br(),
        html.Br(),
        html.Div([
            html.Button('Miller-Rabin', id='do_test', style = {'display': 'inline-block', 'margin-left': '1%', 'margin-right': '1%'})
        ]),
        dcc.Store(id = 'memory_rm', data = [])
    ], id = 'miller_rabin'),
    dcc.Loading(id = 'loading_rm', type = 'default', children = html.Div(id = 'loading_rm_output')),
    html.Br(),
    html.Br(),

    # RSA
    html.H1('RSA'),
    html.Hr(style = {'width': '30%', 'margin-top': '0%', 'margin-bottom': '2%', 'border-top': '1.5px solid black', 'text-align': 'left', 'margin-left': '0'}),
    html.Div([
        html.Div([
            html.Label('Primes', style = {'width': '10%'}),
            dcc.Input(
                id = 'p',
                placeholder = 'Enter a prime',
                style = {'display': 'inline-block', 'width': '15%', 'margin-right': '1%'}
            ),
            dcc.Input(
                id = 'q',
                placeholder = 'Enter a prime',
                style = {'display': 'inline-block', 'width': '15%', 'margin-right': '1%'}
            ),
            html.Button('LCG', id='generate_n', n_clicks=0, style={'display': 'inline-block', 'margin-right': '1%', 'width': '130px'}),
            html.Div([], id='n', style = {}),

        ], style = {'display': 'flex', 'align-items': 'center', 'margin-bottom': '1%'}),
        html.Div([
            html.Label('Public key', style = {'width': '10%'}),
            dcc.Input(
                id = 'e',
                placeholder = 'Public key',
                style = {'display': 'inline-block', 'width': '31%', 'margin-right': '1%'}
            ),
            html.Button('Generate', id='generate_e', n_clicks=0, style={'display': 'inline-block', 'margin-right': '1%'}),
            html.Div([''], id='e_control', style = {}),
        ], style = {'display': 'flex', 'align-items': 'center', 'margin-bottom': '1%'}),
        html.Div([
            html.Label('Private key', style = {'width': '10%'}),
            dcc.Input(
                id = 'd',
                readOnly = True,
                placeholder = 'Private key',
                type = 'text',
                style = {'display': 'inline-block', 'width': '31%', 'margin-right': '1%'}
            ),
            html.Button('Create', id='generate_d', n_clicks=0, style={'display': 'inline-block', 'margin-right': '1%', 'width': '130px', 'text-align': 'center'}),
        ], style = {'display': 'flex',}),
        html.Br(),
        html.Br(),
        html.Div([
            html.Div([
                html.Label('Encrypt', style = {'width': '10%'}),
                dcc.Input(
                    id = 'encrypt_text',
                    placeholder = 'Enter a text you want to encrypt',
                    type = 'text',
                    style = {'display': 'inline-block', 'width': '31%', 'margin-right': '1%'}
                ),
                html.Button('Cipher', id='encrypt_button', n_clicks=0, style={'display': 'inline-block', 'margin-right': '1%', 'width': '130px'}),
                html.Div([''], id = 'maximum_characters')
            ], style = {'display': 'flex', 'margin-bottom': '1%', 'align-items': 'center'}),
            html.Div([
                html.Label('Decrypt', style = {'width': '10%'}),
                dcc.Input(
                    id = 'decrypt_text',
                    placeholder = 'Enter a text you want to decrypt',
                    type = 'text',
                    style = {'display': 'inline-block', 'width': '31%', 'margin-right': '1%'}
                ),
                html.Button('Decipher', id='decrypt_button', n_clicks=0, style={'display': 'inline-block', 'margin-right': '1%', 'width': '130px'})
            ], style = {'display': 'flex'})
        ], id = 'invisible_block')
    ], id = 'rsa'),



    html.Div([
        # reset button
        html.Button('Reset', id='reset-button', style = {'display': 'inline-block', 'margin-left': '1%', 'margin-right': '1%', 'margin-top': '1%'}),
        # <a> element disguised as a button, for closing the app
        html.A('Close', id='close-tab', href= 'JavaScript:window.close()', style = {
        'height': '38px',
        'padding': '0 30px',
        'color': '#555',
        'text-align': 'center',
        'font-size': '11px',
        'font-weight': '600',
        'line-height': '38px',
        'letter-spacing': '.1rem',
        'text-transform': 'uppercase',
        'text-decoration': 'none',
        'white-space': 'nowrap',
        'background-color': 'transparent',
        'border-radius': '4px',
        'border': '1px solid #bbb',
        'cursor': 'pointer',
        'box-sizing': 'border-box',
        'display': 'inline-block', 
        'margin-right': '1%',
        'margin-top': '1%',
        'width': '110px'}),
    ], style= {'display': 'flex'}),
    html.Br()
], className= 'body_banner')

# app.callbacks 
# is used to interact with Dash components
# Output - which components will be uploaded
# Input - when those components properties change, the callback is activated
# State - don´t activate the callback, but their value is loaded in the function
# Inputs and States are loaded into the function in the same order as they are in the decorator
# switch (ctx.triggered_id) decides what to do based on which specific Input triggered the callback
# at the end, the function returns the values which will be assigned to the Output components again in the same order as in the decorator
# more here: https://dash.plotly.com/basic-callbacks


# LCG generator + estimates size of the files with numbers generated by LCG
@app.callback(
    Output('count', 'value'),
    Output('lower', 'value'),
    Output('upper', 'value'),
    Output('memory_lcg', 'data'),
    Output('loading_lcg_output', 'children'),
    Output('estimated_size', 'children'),
    Input('reset-button', 'n_clicks'),
    Input('generate', 'n_clicks'),
    Input('odd_numbers', 'n_clicks'),
    State('count', 'value'),
    State('lower', 'value'),
    State('upper', 'value'),
    State('memory_lcg', 'data'),
    State('lcg_upload', 'value'),
    State('loading_lcg_output', 'children'))
def generate_numbers(reset, generate, odd_numbers, count, lower, upper, memory_lcg, lcg_upload, loading_lcg_output):
    reset_or_generate = ctx.triggered_id
    if reset_or_generate == 'reset-button':
        return None, None, None, False, '', ''
    if reset_or_generate == 'generate':
        c = count
        l = int(lower)
        u = int(upper)
        global data_lcg
        data_lcg = do_lcg(c, l, u)
        return None, None, None, True, '', estimate_size(upper, c)
    if reset_or_generate == 'odd_numbers':
        if lcg_upload == 'Upload':
            return count, lower, upper, memory_lcg, '', loading_lcg_output
        else:
            only_odd = []
            for i in range(len(data_lcg)):
                if data_lcg[i] % 2 == 1:
                    only_odd.append(data_lcg[i])
            data_lcg = only_odd
            return count, lower, upper, memory_lcg, '', loading_lcg_output
    else:
        return None, None, None, False, '', loading_lcg_output


# csv
@app.callback(
    Output('upload_csv', 'disabled'),
    Input('lcg_upload', 'value'))
def upload_disabled(lcg_upload):
    if lcg_upload == 'LCG':
        return True
    else:
        return False

@app.callback(
    Output('memory_csv', 'data'),
    Output('loading_odd_output', 'children'),
    Input('upload_csv', 'contents'),
    Input('odd_numbers', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('lcg_upload', 'value'),
    State('memory_csv', 'data'))
def csv_into_memory(upload_csv, odd_numbers, reset, lcg_upload, memory_csv):
    odd_or_else = ctx.triggered_id
    if odd_or_else == 'upload_csv':
        if upload_csv is not None:
            global data_csv
            data_csv = [int(x) for x in parse_contents(upload_csv)]
            return True, ''
        else:
            return False, ''
    if odd_or_else == 'odd_numbers':
        if lcg_upload == 'Upload':
            only_odd = []
            for i in range(len(data_csv)):
                if data_csv[i] % 2 == 1:
                    only_odd.append(data_csv[i])
            data_csv = only_odd
            return True, ''
        else:
            return memory_csv, ''
    else:
        return False, ''

@app.callback(
    Output('upload_csv', 'contents'),
    Input('remove-button', 'n_clicks'),
    Input('reset-button', 'n_clicks'))
def remove_csv_file(remove, reset):
    return None

@app.callback(
    Output('remove-button', 'style'),
    Input('upload_csv', 'contents'))
def style_remove_button(upload):
    if upload is not None:
        return {'margin-left': '20%', 'background-color': '#0052CC', 'color': 'white'}
    else:
        return {'margin-left': '20%'}

@app.callback(
    Output('upload_csv', 'style'),
    Input('upload_csv', 'contents'))
def upload_color(switch):
    if switch is not None:
        return {
            'width': '190%',
            'lineHeight': '36px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'display': 'inline-block',
            'margin-bottom': '6px',
            'background-color': '#caeceb',
            'opacity': '0.4',
            'color': 'black'
        }
    else:
        return {'width': '190%',
                'lineHeight': '36px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'display': 'inline-block',
                'margin-bottom': '6px'
        }


# Miller-Rabin test
@app.callback(
    Output('memory_rm', 'data'),
    Output('loading_rm_output', 'children'),
    Input('do_test', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('lcg_upload', 'value'),
    prevent_initial_call=True)
def miller_rabin_test(n_clicks, reset, lcg_upload):
    switch = ctx.triggered_id
    if switch == 'do_test':
        if lcg_upload == 'LCG':
            global miller_rabin
            miller_rabin = do_miller_test(data_lcg)
            return True, ''
        else:
            miller_rabin = do_miller_test(data_csv)
            return True, ''
    else:
        return False, ''


# RSA part !!!

# picking randomly p and q from numbers generated by LCG and tested by Miller-Rabin test
@app.callback(
   Output('p', 'value'),
   Output('q', 'value'),
   Input('generate_n', 'n_clicks'),
   Input('reset-button', 'n_clicks'),
   prevent_initial_call=True)
def generate_n(generate, reset):
    switch = ctx.triggered_id
    if switch == 'generate_n':
        random_choose = do_lcg(2, 0, len(miller_rabin))
        while random_choose[0] == random_choose[1]:
            random_choose = do_lcg(2, 0, len(miller_rabin))
        return str(miller_rabin[random_choose[0]]), str(miller_rabin[random_choose[1]])
    else:
        return None, None

# for user to know if inputs p and q are primes (mainly for the case when user fills in the values)
@app.callback(
    Output('n', 'children'),
    Input('p', 'value'),
    Input('q', 'value'),
    prevent_initial_call = True)
def text_n(p, q):
    if p is not None and q is not None:
        if miller_rabin(int(p)) and miller_rabin(int(q)):
            return 'OK'
        else:
            return 'Not primes'
    else:
        return 'Not primes'


# generate e (public key), which has to be a prime smaller than lambda(n)=((p-1) * (q-1)) 
@app.callback(
    Output('e', 'value'),
    Input('generate_e', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('p', 'value'),
    State('q', 'value'),
    prevent_initial_call = True)
def e(generate, reset, p, q):
    switch = ctx.triggered_id
    if switch == 'generate_e':
        global data_n
        global data_lambdan
        data_n = int(p) * int(q)
        data_lambdan = (int(p)-1)*(int(q)-1)
        g = 100
        a = do_lcg(g, 0, data_lambdan - 1)
        b = do_miller_test(a)
        while len(b) == 0:
            g += 100
            a = do_lcg(g, 0, data_lambdan - 1)
            b = do_miller_test(a)
        return str(max(b))
    else:
        return None

# for user to know if e is a prime and its greatest common divisor with lambda(n) is 1 (mainly for the case when user fills in the values)
@app.callback(
    Output('e_control', 'children'),
    Input('e', 'value'),
    Input('reset-button', 'n_clicks'),
    State('p','value'),
    State('q','value'),
    prevent_initial_call = True)
def text_e(e, reset, p, q):
    switch = ctx.triggered_id
    if switch == 'e':
        if miller_rabin(int(e)) == False and gcd(e, data_lambdan) == False:
            return 'Not a prime and the greatest common divisor with lambda(n) is not 1'
        elif miller_rabin(int(e)) == False:
            return 'Not a prime'
        elif gcd(int(e), data_lambdan) == False:
            return 'The greatest common divisor with lambda(n) is not 1'
        else:
            return 'OK'
    else:
        return ''


# generate d (private key) based on public key and lambda(n), cannot be entered by user
@app.callback(
    Output('d', 'value'),
    Input('generate_d', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('e', 'value'),
    prevent_initial_call=True)
def generate_private_key(click, reset, e):
    switch = ctx.triggered_id
    if switch == 'generate_d':
        global data_e
        data_e = int(e)
        return str(modinv(data_e, data_lambdan))
    else:
        return None



# encrypts a message inserted by user 
@app.callback(
    Output('encrypt_text', 'value'),
    Input('encrypt_button', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('encrypt_text', 'value'),
    State('e', 'value'),
    prevent_initial_call=True)
def encrypt(n_clicks, reset, encrypt_text, e):
    switch = ctx.triggered_id
    if switch == 'encrypt_button':
        global boolean_for_message
        global just_used_button
        boolean_for_message = True
        just_used_button = True
        bytes = str.encode(encrypt_text)
        number = int.from_bytes(bytes, byteorder='little')
        return str(pow(number, data_e, data_n))
    else:
        return None

# decrypts the cipher code
@app.callback(
    Output('decrypt_text', 'value'),
    Input('decrypt_button', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('decrypt_text', 'value'),
    State('d', 'value'),
    prevent_initial_call=True)
def decrypt(n_clicks, reset, decrypt_text, d):
    switch = ctx.triggered_id
    if switch == 'decrypt_button':
        number = pow(int(decrypt_text), int(d), data_n)
        byte = number.to_bytes(number.bit_length(), byteorder='little')
        a = byte.decode()
        return a.rstrip('\x00')
    else:
        return ''



# messages
@app.callback(
    Output('maximum_characters', 'children'),
    Input('encrypt_button', 'disabled'),
    State('encrypt_text', 'value'))
def encrypt_button_color(button, encrypt_text):
    if button == True:
        if encrypt_text is not None and boolean_for_message == False:
            return 'Too many characters! Use bigger primes for longer message.'
        else:
            return ''
    else:
        return ''

# style and disable buttons
@app.callback(
    Output('generate', 'disabled'),
    Input('count', 'value'),
    Input('lower', 'value'),
    Input('upper', 'value'))
def disable_generate(count, lower, upper):
    if count is not None and lower is not None and upper is not None and int(lower) < int(upper):
        return False
    else:
        return True

@app.callback(
    Output('generate', 'style'),
    Input('generate', 'disabled'))
def button_color(stateofbutton):
    if stateofbutton == False:
        return {'display': 'inline-block', 'background-color': '#0052CC', 'color': 'white', 'margin-left': '1%', 'margin-right': '1%'}
    else:
        return {'display': 'inline-block', 'margin-left': '1%', 'margin-right': '1%'}


@app.callback(
    Output('btn_csv', 'disabled'),
    Output('btn_txt', 'disabled'),
    Input('memory_lcg', 'data'))
def lcg_buttons_disabled(memory_lcg):
    if memory_lcg == True:
        return False, False
    else:
        return True, True

@app.callback(
    Output('btn_csv', 'style'),
    Output('btn_txt', 'style'),
    Input('btn_csv', 'disabled'))
def lcg_buttons_color(btncsv):
    if btncsv == False:
        return {'background-color': '#0052CC', 'color': 'white'}, {'background-color': '#0052CC', 'color': 'white'}
    else:
        return {}, {}


@app.callback(
    Output('odd_numbers', 'disabled'),
    Input('memory_lcg', 'data'),
    Input('memory_csv', 'data'),
    Input('lcg_upload', 'value'))
def odd_button_disabled(memory_lcg, memory_csv, lcg_upload):
    if lcg_upload == 'LCG':
        if memory_lcg == True:
            return False
        else:
            return True
    else:
        if memory_csv == True:
            return False
        else:
            return True

@app.callback(
    Output('odd_numbers', 'style'),
    Input('odd_numbers', 'disabled'))
def odd_button_color(stateofbutton):
    if stateofbutton == False:
        return {'display': 'inline-block', 'margin-bottom': '2%', 'background-color': '#0052CC', 'color': 'white'} 
    else:
        return {'display': 'inline-block', 'margin-bottom': '2%'}


@app.callback(
    Output('do_test', 'disabled'),
    Input('lcg_upload', 'value'),
    Input('memory_csv', 'data'),
    Input('memory_lcg', 'data'))
def disable_test(lcg_upload, memory_csv, memory_lcg):
    if lcg_upload == 'LCG':
        if memory_lcg == True:
            return False
        else:
            return True
    else:
        if memory_csv == True:
            return False
        else:
            return True

@app.callback(
    Output('do_test', 'style'),
    Input('do_test', 'disabled'))
def test_button_color(stateofbutton):
    if stateofbutton == False:
        return {'display': 'inline-block', 'background-color': '#0052CC', 'color': 'white', 'margin-left': '1%', 'margin-right': '1%'}
    else:
        return {'display': 'inline-block', 'margin-left': '1%', 'margin-right': '1%'}


@app.callback(
    Output('btn_csv_rm', 'disabled'),
    Output('btn_txt_rm', 'disabled'),
    Input('memory_rm', 'data'))
def lcg_buttons_disabled(memory_rm):
    if memory_rm == True:
        return False, False
    else:
        return True, True

@app.callback(
    Output('btn_csv_rm', 'style'),
    Output('btn_txt_rm', 'style'),
    Input('btn_csv_rm', 'disabled'))
def lcg_buttons_color(btncsv):
    if btncsv == False:
        return {'background-color': '#0052CC', 'color': 'white'}, {'background-color': '#0052CC', 'color': 'white'}
    else:
        return {}, {}


@app.callback(
    Output('generate_n', 'disabled'),
    Input('memory_rm', 'data'))
def activate_n(memory):
    if memory == True and len(miller_rabin) > 1:
        return False
    else:
        return True

@app.callback(
    Output('generate_n', 'style'),
    Input('generate_n', 'disabled'))
def n_button_color(stateofbutton):
    if stateofbutton == False:
        return {'display': 'inline-block', 'margin-right': '1%', 'width': '130px', 'background-color': '#0052CC', 'color': 'white'}
    else:
        return {'display': 'inline-block', 'margin-right': '1%', 'width': '130px'}


@app.callback(
    Output('generate_e', 'disabled'),
    Input('n', 'children'))
def control_e(n):
    if n == 'OK':
        return False
    else:
        return True

@app.callback(
    Output('generate_e', 'style'),
    Input('generate_e', 'disabled'))
def e_button_color(stateofbutton):
    if stateofbutton == False:
        return {'display': 'inline-block', 'margin-right': '1%', 'background-color': '#0052CC', 'color': 'white'}
    else:
        return {'display': 'inline-block', 'margin-right': '1%'}


@app.callback(
    Output('generate_d', 'disabled'),
    Input('e_control', 'children'),
    Input('n', 'children'))
def activate_privatekey(e, n):
    if e == 'OK' and n == 'OK':
        return False
    else:
        return True

@app.callback(
    Output('generate_d', 'style'),
    Input('generate_d', 'disabled'))
def d_button_color(stateofbutton):
    if stateofbutton == False:
        return {'display': 'inline-block', 'margin-right': '1%', 'width': '130px', 'text-align': 'center', 'background-color': '#0052CC', 'color': 'white'}
    else:
        return {'display': 'inline-block', 'margin-right': '1%', 'width': '130px', 'text-align': 'center'}


@app.callback(
    Output('encrypt_button', 'disabled'),
    Input('encrypt_text', 'value'),
    Input('p', 'value'),
    Input('q', 'value'),
    Input('e', 'value'))
def activate_encrypt(encrypt_text, p, q, e):
    switch = ctx.triggered_id
    if switch == 'encrypt_text':
        global boolean_for_message
        global just_used_button
        if just_used_button == True:
            just_used_button = False
        else:
            boolean_for_message = False
    if e is not None and encrypt_text is not None:
        try:
            if int(p) * int(q) == data_n and int(e) == data_e and len(str.encode(encrypt_text)) <= countbytes(data_n):
                return False
            else: 
                return True
        except ValueError:
            pass
    else:
        return True    
    
@app.callback(
    Output('encrypt_button', 'style'),
    Input('encrypt_button', 'disabled'))
def encrypt_button_color(stateofbutton):
    if stateofbutton == False:
        return {'display': 'inline-block', 'margin-right': '1%', 'width': '130px', 'background-color': '#0052CC', 'color': 'white'}
    else:
        return {'display': 'inline-block', 'margin-right': '1%', 'width': '130px'}


@app.callback(
    Output('decrypt_button', 'disabled'),
    Input('d', 'value'),
    Input('decrypt_text', 'value'),
    Input('p', 'value'),
    Input('q', 'value'),
    Input('e', 'value'))
def activate_decrypt(d, decrypt_text, p, q, e):
    if d is not None and decrypt_text is not None and q is not None and p is not None and e is not None:
        try:
            if int(p) * int(q) == data_n and int(e) == data_e:
                return False
            else:
                return True
        except ValueError:
            print('Enter a number!')
    else:
        return True    

@app.callback(
    Output('decrypt_button', 'style'),
    Input('decrypt_button', 'disabled'))
def decrypt_button_color(stateofbutton):
    if stateofbutton == False:
        return {'display': 'inline-block', 'margin-right': '1%', 'width': '130px', 'background-color': '#0052CC', 'color': 'white'}
    else:
        return {'display': 'inline-block', 'margin-right': '1%', 'width': '130px'}



# download
@app.callback(
    Output('download-csv', 'data'),
    Input('btn_csv', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    prevent_initial_call=True)
def func(n_clicks, reset):
    switch = ctx.triggered_id
    if switch == 'btn_csv':
        df_lcg = pd.DataFrame(data_lcg)
        return dcc.send_data_frame(df_lcg.to_csv, 'lcg.csv', index = False, header=False)
    else:
        return None

@app.callback(
    Output('download-txt', 'data'),
    Input('btn_txt', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    prevent_initial_call=True)
def func(n_clicks, reset):
    switch = ctx.triggered_id
    if switch == 'btn_txt':
        data = [str(x) for x in data_lcg]
        return dict(content=',\n'.join(data), filename='lcg.txt') 
    else:
        return None


@app.callback(
    Output('download_csv_rm', 'data'),
    Input('btn_csv_rm', 'n_clicks'),
    prevent_initial_call=True)
def func(n_clicks):
    df = pd.DataFrame(miller_rabin)
    return dcc.send_data_frame(df.to_csv, 'rm.csv', index = False, header=False)

@app.callback(
    Output('download_txt_rm', 'data'),
    Input('btn_txt_rm', 'n_clicks'),
    prevent_initial_call=True)
def func(n_clicks):
    data = [str(x) for x in miller_rabin]
    return dict(content=',\n'.join(data), filename='rm.txt')
  

# starts the Dash app in a new browser tab
port = 8050
def open_browser():
	webbrowser.open_new("http://localhost:{}".format(port))

if __name__ == '__main__':
    Timer(1, open_browser).start();
    app.run_server(debug=False, port=port)

