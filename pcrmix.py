#!/usr/bin/env python
# coding: utf-8

"""
For use in Jupyter or similar environments, import and run the jupyter_pcr function
"""
import json
import sys
from collections import OrderedDict
from datetime import datetime as dtime, timedelta as dt_delta
from os import listdir, remove as rm
from os.path import isfile, join as pjoin, abspath, basename, getctime as change_time
from random import randint
from textwrap import fill as twrap_fill
from typing import Any

from flask import Flask, render_template, request, session, jsonify
from numpy import isnan, nan
from pandas import DataFrame, Series, __version__ as pdvers, set_option as pd_setopt
# from pandas import 
from json import dumps as jdumps

from common_utils import DotDict, safesplit, dkey_search, newer_than

sys.tracebacklimit = 0

TEMPLATE_DIR = abspath('./templates')
STATIC_DIR = abspath('./static')
MIXDIR = 'mixes'
CURRENT_TABLE = None
PARAMETERS = None

# PAGE_CURRENT_RENDER = None
# STORED_RENDER = None

web_pcr = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATE_DIR, )
web_pcr.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
web_pcr.config['SECRET_KEY'] = (
  ''.join(['ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz012345678@#%@$!:@#$%^&*()+=+,-./:?'[
             randint(0, 85)] for i in range(100)]))

# web_pcr_htmx = HTMX(web_pcr)
web_pcr_tablename = 'pcr_reagents_web.tsv'

BROWSERS = ['firefox', 'netscape', 'galeon', 'epiphany', 'skipstone', 'mosaic', 'opera', 'grail', 'links', 'elinks',
            'lynx', 'w3m', 'windows-default', 'macosx', 'safari', 'google-chrome', 'chrome', 'chromium',
            'chromium-browser']


class PcrRecipe(DataFrame):
  def make_html(self):
    # precision for numbers
    # pandas.set_option('display.precision', 2)
    # options.display.precision = 2

    if newer_than(pdvers, '1.4'):
      ms = self.style.format(precision=2).hide(axis='index')
    else:
      ms = self.style.format(precision=2).hide_index()

    ms = ms.set_properties(subset=['Reagents'], **{'font-weight': 'bold',
                                                   'font-size': '16px',
                                                   'font-family': 'consolas',
                                                   'text-align': 'left'})

    ms = ms.set_properties(subset=self.columns[:3], **{'text-align': 'left'})
    ms = ms.set_properties(subset=self.columns[3:], **{'text-align': 'right'})
    # ms = ms.set_properties(subset=['c stock', 'c work'], **{'text_align': 'right'})

    ms.set_table_styles([{'selector': 'th', 'props': [('background-color', '#3A6191FF'),
                                                      ('color', 'white'),
                                                      ('font-size', '16px'),
                                                      ('font-family', 'consolas'),
                                                      ('padding-left', '10px'),
                                                      ('padding-right', '10px'),
                                                      ('text-align', 'left')
                                                      ]},
                         {'selector': 'table', 'props': [('width', '400px'),
                                                         ('border-collapse', 'collapse'),
                                                         ('border', 'none'),
                                                         ('border-spacing', '0px'),
                                                         ('white-space', 'nowrap'),
                                                         ('user-select', 'none'),
                                                         ('cursor', 'pointer')
                                                         ]},
                         {'selector': 'td', 'props': [('padding-left', '10px'),
                                                      ('padding-right', '10px'),
                                                      ('height', '25px'),
                                                      ('border', 'none'),
                                                      ('font-family', 'consolas'),
                                                      ('font-size', '14px'),
                                                      ]},
                         {'selector': 'tr', 'props': [('height', '25px'),
                                                      ('border-top', '1px dotted lightblue')]},
                         {'selector': 'tr:first-chield', 'props': [('border-top', 'none')
                                                                   ]},
                         {'selector': 'tr:nth-child(odd)', 'props': [('background-color', '#f5fbff')]},
                         {'selector': 'tr:nth-last-child(2)',
                          'props': [('background-color', 'SkyBlue'), ('color', 'black')]},

                         ])

    html = ms.to_html(float_format='%0.2f')  # if newer_than(pdvers, '1.4') else ms.render()
    html = html.replace(' table {', ' {')

    # with open('pcrmix_tmp.html', 'w') as wf:
    #     wf.write(html)

    return html


def tryfloat(a: str, defval=None):
  try:
    return float(a)
  except ValueError:
    return a if defval is None else defval


def mg(d: dict, keylist=(), default: Any = 0, aliases=False):
  """
  Searches for provided keys in dictionary and returns one value if at least one key found
  when aliases==True or list of values, corresponding all found keys, when
  aliases==False
  """

  if not any(key in d for key in keylist):
    return default
  keys_existed = [key for key in keylist if key in d]
  if aliases:
    if all(d[key] == d[keys_existed[0]] for key in keys_existed):
      return d[keys_existed[0]]
    else:
      raise ValueError('The keys provided address non equal values')
  else:
    return tuple(d[key] for key in keys_existed)


def table_check(filename: str, log=False, extension=''):
  if log:
    print('Testing:', filename)
  if isfile(filename) and filename.endswith(extension):
    with open(filename, 'r') as ofile:
      for line in ofile:
        if line.startswith('#') or line.startswith('['):
          continue
        else:
          try:
            reagent, cstock, cwork, units = line.split('\t', maxsplit=3)
            1 / len(reagent)
            cstock = float(cstock)
            cwork = float(cwork)
            1 / len(units)
          except:
            if log:
              print('not passed: check 1')
            return False
    if log:
      print('passed check')
    return True
  else:
    if log:
      print('not passed: check 2')
    return False


def load_reagents(src: Any, srctype='filename'):
  if srctype == 'filename' and table_check(src):
    with open(src, 'r', encoding='utf-8') as rfile:
      data = rfile.readlines()
      rtable = OrderedDict((line.split('\t')[0], list(map(tryfloat, line.strip(
        '\n').split('\t')[1:]))) for line in data if not line[0] in ('#', '['))

      additional = next(filter(lambda line: line[0] == '[' and line[-1] == ']', data), '').strip('[]')

      mixvol, dnavol, number, hide_list = mg(json.loads(additional),
                                             keylist=('mix_volume', 'dna_volume', 'n_samples', 'hidelist'),
                                             default=(25, 5, 10, []),
                                             aliases=False
                                             ) if additional else [25, 5, 10, []]

  elif srctype == 'json':
    web_data = src.get_json()
    mixvol, dnavol, number = web_data['mixParameters']
    rtable = OrderedDict(web_data['reagentTable'])
    hide_list = web_data['hidelist']
  else:
    rtable, [mixvol, dnavol, number, hide_list] = OrderedDict({}), [25, 5, 10, []]

  return rtable, [mixvol, dnavol, number, hide_list]


def __save_reagents_table(filename: str, reagents: OrderedDict, additional_fields={}, subdir=''):
  with open(pjoin(subdir, filename), 'w', encoding='utf-8') as wf:
    wf.write('#reagents\tCstock\tCwork\tUnits\n')
    for reagent in reagents:
      wf.write(reagent + '\t' + '\t'.join(map(str, reagents[reagent])) + '\n')

    # f"[{','.join([f'{key}={additional_fields[key]}' for key in additional_fields if key != 'hidelist'])},]"
    adddata = jdumps(additional_fields)
    wf.write(f'[{adddata}]')


# PCR MIX
def pcrmix_calc(reagents: OrderedDict, loc_params: DotDict):
  """
  reagents: dict - table of the pcr reagents. Format: {reagent1: [Cstock, Cwork, Units], ...}
  loc_params.
      .volume: float - one sample mix volume
      .number: float - the number of samples
      .template_volume: float - volume of the template solution
      .hide: list of reagents to hide in mix
      .exclude: list of reagents to exclude from mix
      .add_reagents: dictionary of reagents to add to mix (of format similar to reagents format)
      .change: dictionary of reagent, to redefine concentrations

  """
  dna_solution_volume = loc_params[('template', 5),]  # arguments.get('template_volume', 5)
  sample_number = loc_params[('number', 0),]
  mix_volume = loc_params[('volume', 25),]
  hide = loc_params[('hide', []),]

  exclude = loc_params[('exclude', []),]
  for reagent in exclude:
    reagents.pop(reagent, 0)

  change = loc_params[('change', {}),]
  # lower() is used since all "arguments" being stored lowered
  for r in reagents:
    if r in change:
      reagents[r] = change[r]

  add_reagents = [reagent.split(',') for reagent in loc_params[('add_reagents', []),]]
  add_reagents = {r[0]: r[1:] for r in add_reagents}
  reagents.update(add_reagents)

  reagents_list = list(map(lambda key: key if not key.lower().startswith('f:') and not key.lower().startswith(
    'r:') else key[2:], reagents.keys()))

  c_stock = Series({reagent: float(mg(reagents, keylist=[reagent, 'f:' + reagent, 'r:' + reagent], default=None,
                                      aliases=True)[0]) for reagent in reagents_list})
  c_work = Series({reagent: float(mg(reagents, keylist=[reagent, 'f:' + reagent, 'r:' + reagent], default=None,
                                     aliases=True)[1]) for reagent in reagents_list})
  sunits = Series({reagent: mg(reagents, keylist=[reagent, 'f:' + reagent, 'r:' + reagent], default='',
                               aliases=True)[2] for reagent in reagents_list})

  mix = DataFrame({'Reagents': reagents_list, 'C stock': c_stock, 'C work': c_work})
  mix.set_index('Reagents', inplace=True)
  pd_setopt("display.precision", 2)  # may be it should be removed
  mix['Vx1 (ul)'] = (mix['C work'] / mix['C stock']) * mix_volume
  mix.loc['H2O', 'Vx1 (ul)'] = mix_volume - mix['Vx1 (ul)'].sum() - dna_solution_volume
  mix.loc['Template', 'Vx1 (ul)'] = dna_solution_volume
  mix[f'Vx{sample_number} (ul)'] = mix['Vx1 (ul)'] * sample_number
  mix.loc['Total', 'Vx1 (ul)'] = mix['Vx1 (ul)'].sum()
  mix.loc['Total', f'Vx{sample_number} (ul)'] = mix[f'Vx{sample_number} (ul)'].sum()
  dispense = mix.loc['Total', 'Vx1 (ul)'] - dna_solution_volume - mix.loc[mix.index.isin(hide), 'Vx1 (ul)'].sum()
  mix.loc['Dispense', 'Vx1 (ul)'] = dispense if dispense > 0 else '0'
  # print(mix.loc['Dispense', 'Vx1 (ul)'])
  try:
    mix['C stock'] = mix['C stock'].apply(lambda x: str(x) if not isnan(x) else nan) + ' ' + sunits
  except:
    print(mix['C stock'])
    print(sunits)
  mix['C work'] = mix['C work'].apply(lambda x: str(x) if not isnan(x) else nan) + ' ' + sunits
  mix = mix[mix['Vx1 (ul)'] != 0]
  mix = mix[~mix.index.isin(hide)]
  mix = mix[mix['Vx1 (ul)'].notna()].fillna('').reset_index()
  return PcrRecipe(mix)


def info(show=True):
  inf = open('info.txt', 'r', encoding='utf-8').read()
  info_text = '\n\n'.join([twrap_fill(line, 80) for line in inf])
  print(info_text if show else '')
  return info_text


def rlist(reagents, add_reagents, change, exclude):
  outline = '\ntable: \n'
  for r in reagents:
    outline = outline + r + '\t' + '\t'.join(map(str, reagents[r]))

  outline = outline + '\nexclude: \n'
  for e in exclude:
    outline = outline + e

  outline = outline + '\nadd: \n'
  for a in add_reagents:
    reag, stock, work, units = a.split(',')
    outline = outline + reag + '\t' + '\t'.join([stock, work, units])

  outline = outline + '\nchange: \n'
  for c in change:
    reag, stock, work, units = safesplit(c, ',', minparts=4)
    outline = outline + reag + '\t' + '\t'.join([stock, work, units])

  return outline + '\n'


def list_tables(dirpath=''):
  # print(os.path.abspath(dirpath) + ':')
  return list(filter(lambda fname: table_check(pjoin(dirpath, fname), extension='tsv') and fname !=
                     'last_reagents_table.tsv', listdir(dirpath)))


def extract_args(run_args: dict | list):
  # sysargs = sys.argv
  arguments = {}
  if type(run_args) is list:
    for arg in map(lambda key: key[2:] if key.startswith('--') else key, run_args):
      if '=' in arg:
        argname, value = safesplit(line=arg, key='=', minparts=2,
                                   maxsplit=1) if '~' not in arg else ['change', arg.replace('=', ',')[1:]]
        arguments[argname] = value if argname not in arguments else (arguments[argname] + '|' + value)
      else:
        arguments[arg] = True
      arguments = {argument.lower(): arguments[argument] for argument in arguments}
  else:
    arguments = run_args

  forward = mg(arguments, ('forward', 'for', 'f'), '', True)
  forward = forward if forward.lower().startswith('f:') or len(forward) < 1 else ('f:' + forward)
  reverse = mg(arguments, ('reverse', 'rev', 'r'), '', True)
  reverse = reverse if reverse.lower().startswith('r:') or len(reverse) < 1 else ('r:' + reverse)

  return DotDict({
    'browser_name': mg(arguments, keylist=('browser', 'Browser', 'BROWSER'), default='', aliases=True),
    'forward': forward,
    'reverse': reverse,
    'volume': tryfloat(mg(arguments, ('volume', 'vol', 'v'), 25, True)),
    'number': tryfloat(mg(arguments, ('number', 'num', 'n'), 10, True)),
    'output': mg(arguments, ('o', 'out', 'output', 'html'), '', True),
    'template': tryfloat(mg(arguments, ('template_volume', 'tv', 'dna_volume',
                                        'dna_v', 'dnav', 'tempv', 'temp_v', 'sample',
                                        'sv', 'sample_volume', 'sample_v'), 5, True)),
    'table_name': mg(arguments, ('table', '--table'), 'pcr_reagents.tsv', aliases=True),
    'hide': arguments.get('hide', '').replace(';', '|').split('|'),
    'exclude': mg(arguments, ('ex', 'exclude'), '', True).replace(';', '|').split('|'),
    'add_reagents': arguments['add'].replace(';', '|').split('|') if 'add' in arguments else [],
    'silent': mg(arguments, keylist=('--silent', 'silent'), default=False, aliases=True),
    'nopromt': arguments.get('nopromt', False),
    'change': arguments['change'].replace(';', '|').split('|') if 'change' in arguments else [],
    'tlist': False if 'tlist' not in arguments else True if (
      type(arguments['tlist']) is bool and arguments['tlist']) else arguments['tlist'],
    'showinfo': mg(arguments, keylist=('help', 'h', 'H', '--help', 'Help', '--Help', '-h', '-H',
                                       'info', '--info'), default=False, aliases=True),
    'web': arguments.get('web', False),
    'list': arguments.get('list', False),
    'debug': arguments.get('debug', ''),
    'run_port': arguments.get('port', 5000)
  })


def _cli_table_request(mix_dir=''):
  """
  Do not use in Jupyter. Try not to use it at all...
  """

  table_list = list(filter(lambda tablename: tablename != 'last_reagents_table.tsv', list_tables(dirpath=mix_dir)))

  last = 'enter "0" to choose last table used, '
  last_table_existed = 'last_reagents_table.tsv' in listdir(mix_dir)  # check last used table existence

  print(f'Enter correct filename or choose one from numbers listed, '
        f'{last if last_table_existed else ""}"e" or "exit" \nto stop program')

  for num, fname in enumerate(table_list):
    print(f'{num + 1}) {fname}')

  table_name = ''
  exits = ['e', 'exit', 'Exit', 'EXIT', 'E']

  # wait for table name - one from pregenerated list of table from working directory or any correct table file
  while table_name not in table_list + ['last_reagents_table.tsv'] if last_table_existed else []:
    table_name = input('> ')
    if table_name in exits:
      table_name = None
      break
    elif table_name.isdigit() and int(table_name) in range(0, len(table_list) + 1):
      table_name = (['last_reagents_table.tsv'] + table_list)[int(table_name)]
    print(table_name, 'chosen.')
  return pjoin(mix_dir, table_name) if table_name else None


def configure_reagents(reagents: OrderedDict, loc_params: DotDict):
  if loc_params.forward or loc_params.rewerse:
    # just changes f:some_primer and r:some_primer to the name provided (if provided) in command line
    reagents = OrderedDict([(loc_params.forward if r.lower().startswith('f:')
                             else loc_params.rewerse if r.lower().startswith('r:')
                             else r, reagents[r]) for r in reagents])

  for ch in loc_params[('change', []),]:  # [] - default value used in case there is no 'change' in parameters
    key = dkey_search(reagents, ch)
    if key:
      reag_ch, stock_ch, work_ch, units_ch = safesplit(ch, ',', minparts=4,
                                                       maxsplit=3)  # how to change mixture
      stock, work, units = reagents[key]
      # find what to change
      if len(ch.split(',')) == 2:
        work = tryfloat(stock_ch)
      elif len(ch.split(',')) == 4:
        work = tryfloat(work_ch, work)
        stock = tryfloat(stock_ch, stock)
        units = units_ch if units_ch else units
      else:
        break
      reagents[key][0], reagents[key][1], reagents[key][2] = stock, work, units
  return reagents


def __default_name():
  file_list = listdir()
  n = 0
  while f'PCR_mix_{hex(n)}.html' in file_list:
    n += 1
  return f'PCR_mix_{hex(n)}.html'


def mix_prep(local_parameters=DotDict({}), table_src='local', web_form_data=None):  # , interactive=False):
  mix = None
  reagents = OrderedDict()
  mix_volume, n_samples, dna_volume, hidelist = None, None, None, []
  if table_src.lower() == 'local':
    table_name = __correct_table_name(local_parameters.table_name, default='', dirpath=MIXDIR)
    if table_name:
      reagents = configure_reagents(load_reagents(table_name)[0], loc_params=local_parameters)
      if len(reagents) == 0:
        print('Empty reagent list.')
      elif local_parameters.list:
        print(rlist(reagents, local_parameters.add_reagents, local_parameters.change, local_parameters.exclude))
      else:
        mix = pcrmix_calc(reagents=reagents, loc_params=local_parameters)
    else:
      raise ValueError('Table name not provided')
      # mix_html = mix.make_html()
  elif table_src.lower() in ['web', 'ajax'] and web_form_data:
    reagents, [mix_volume, dna_volume, n_samples, hidelist] = load_reagents(src=web_form_data,
                                                                            srctype='json')
    mix_volume = tryfloat(mix_volume, 0)
    n_samples = tryfloat(n_samples, 0)
    dna_volume = tryfloat(dna_volume, 0)
    hidelist = list(
      map(lambda reag: reag[2:] if reag.startswith('f:') or reag.startswith('r:') else reag, hidelist))
    mix = pcrmix_calc(reagents=reagents, loc_params=DotDict({'volume': mix_volume, 'number': n_samples,
                                                             'template': dna_volume, 'hide': hidelist}))

  __save_reagents_table('last_reagents_table.tsv', reagents=reagents, subdir=MIXDIR)
  return mix, reagents, {'mix_volume': mix_volume,
                         'n_samples': n_samples,
                         'dna_volume': dna_volume,
                         'hidelist': hidelist}


def mix_render(mix=None, local_parameters=None, mode='cli'):
  if mix:
    mix_html = mix.make_html()
    # html_fname = local_parameters.output if len(local_parameters.output) > 0 else __default_name()
    silent = local_parameters.silent
    if mode == 'cli' and mix_html:
      html_fname = local_parameters.output if len(local_parameters.output) > 0 else __default_name()
      if not silent:
        open(html_fname, 'w').write(mix_html)
      import webbrowser
      try:
        webbrowser.get(local_parameters.browser_name if local_parameters.browser_name else '').open(html_fname)
      except:  # webbrowser.Error:
        webbrowser.get().open(html_fname)
    elif mode == 'jupyter' and mix_html:
      from IPython.display import display, HTML
      display(HTML(mix_html))
  else:
    print('Mix has not been assembled.')


def __correct_table_name(name_to_check='', default='', dirpath=''):
  class ReagentTableError(Exception):
    pass

  full_path = pjoin(dirpath, name_to_check)
  full_dft_path = pjoin(dirpath, default)

  if table_check(name_to_check):
    table_name = name_to_check
  elif table_check(full_path):
    table_name = full_path
  elif table_check(default):
    table_name = default
  elif table_check(full_dft_path):
    table_name = full_dft_path
  else:
    raise ReagentTableError(f'Given names ({name_to_check} | {default}) do not match any reagent tables')
  return table_name


# jupyter ===============================================================================================
def jupyter_pcr(*commands, **args):
  if 'browser' not in args:
    args['browser'] = 'jupyter'
  for command in commands:
    args[command] = True
  jup_parameters = extract_args(args)
  jmix_object, jreag_table = mix_prep(local_parameters=jup_parameters)
  mix_render(jmix_object, local_parameters=jup_parameters, mode='jupyter')


# web pcr section ========================================================================================

# @web_pcr.before_request
# def before_request():
#     print('Redirecting to https version')
#     if request.url.startswith('http://'):
#         url = request.url.replace('http://', 'https://', 1)
#         code = 301
#         return redirect_request(url, code=code)

def __load_ac_rnames():
  with open(pjoin('templates', 'auto_complete_rList.tsv'), 'r', encoding='utf-8') as rfile:
    try:
      ac_rlist = rfile.read().split('\n')
    except FileNotFoundError:
      ac_rlist = []
  return ac_rlist


@web_pcr.route('/')
def index(table_name='', is_session_id=False):
  if not is_session_id and table_name:
    dirpath = ''
  elif not is_session_id and not table_name:
    table_name = parameters.get('table_name', '')
    dirpath = MIXDIR
  elif is_session_id:
    dirpath = 'sessions'
  else:
    dirpath = ''

  table_name = pjoin(dirpath, table_name)

  editor_reagents, [mix_volume, dna_volume, sample_number, hidelist] = load_reagents(table_name, srctype='filename')

  reagent_names = list(editor_reagents.keys())
  table_names = list_tables(dirpath=MIXDIR)

  html = render_template('mix_parameters.html', reagent_table=editor_reagents,
                         reagent_names=reagent_names, enumerate=enumerate,
                         tableName=basename(table_name), tables=table_names,
                         autocomplete_rnames=__load_ac_rnames(),
                         sample_number=sample_number if sample_number else 10,
                         reaction_volume=mix_volume if mix_volume else 25,
                         dna_volume=dna_volume if dna_volume else 5,
                         hide_list=hidelist
                         )

  return html


@web_pcr.route("/reload", methods=["GET"])
def web_reload():
  fname = request.args.get('file')
  table_name = __correct_table_name(name_to_check=fname, default='', dirpath=MIXDIR)
  print('\nReloading: ', table_name, '\n')
  return index(table_name)


@web_pcr.route('/<path:mix_id>')
def session_restore(mix_id):
  mix_id = mix_id.upper()
  session_fname = f'session_{mix_id}'
  # full_name = pjoin('sessions', session_fname)
  if session_fname in listdir('sessions'):
    session['pmix_session'] = mix_id
    return index(table_name=session_fname, is_session_id=True)
  else:
    print(f'Something wrong with session table {mix_id}')
    return (f"<html><body><span style='margin: 50px; font-size: 24px; color: darkgray;'> "
            f"Session {mix_id} was not found. <a style='border: 1px dotted silver' "
            f"href='/'>Start new</a>.</span></body></html>")


@web_pcr.route("/render", methods=['POST'])
def web_mix_render():
  web_mix_object, web_reagents_table, reaction_parameters = mix_prep(table_src='ajax', web_form_data=request)
  html = web_mix_object.make_html()
  if 'pmix_session' not in session:  # set ID for MIX preset to allow its usage in different clients
    session_id = id_gen()
    session['pmix_session'] = session_id
  else:
    session_id = session['pmix_session']
  store_session(session_name=session_id, table=web_reagents_table, react_params=reaction_parameters)
  response = [html, session_id]
  return response


# def form_render(table_name, **keyparams):
#     editor_reagents = load_reagents(table_name)[0]
#     reagent_names = list(editor_reagents.keys())
#     table_names = list_tables(dirpath=MIXDIR)
#     return render_template('mix_parameters.html', reagent_table=editor_reagents,
#                            reagent_names=reagent_names, enumerate=enumerate,
#                            tableName=basename(table_name), tables=table_names,
#                            autocomplete_rnames=__load_ac_rnames(),
#                            sample_number=keyparams.get('sampe_number', 10),
#                            reaction_volume=keyparams.get('reaction_volume', 25),
#                            dna_volume=keyparams.get('dna_volume', 5),
#                            sv_units=keyparams.get('sv_units', 'ul')
#                            )


def clear_old_sessions():
  def __is_old_(file_name):
    created_time = dtime.fromtimestamp(change_time(file_name))
    return (dtime.now() - created_time) > dt_delta(days=1)

  session_list = listdir('sessions')
  for sID_fname in session_list:
    session_file_name = pjoin('sessions', sID_fname)
    if __is_old_(file_name=session_file_name):
      rm(session_file_name)
      session_list.remove(sID_fname)


def store_session(session_name, table, react_params: dict):
  global CURRENT_TABLE

  # if table != CURRENT_TABLE:
  fname = f'session_{session_name}'
  __save_reagents_table(fname, table, subdir='sessions', additional_fields=react_params)
  CURRENT_TABLE = table


def id_gen():
  sessions_list = listdir('sessions')
  new_id = None
  sindex = 0
  while (not new_id) or (f'session_{new_id}' in sessions_list):
    sindex += 1
    new_id = ('SO' + hex(sindex)[1:]).upper()
  return new_id


# ========================================================================================================
if __name__ == "__main__":
  # global PARAMETERS
  parameters = extract_args(sys.argv)
  # PARAMETERS = parameters
  AC_REAG_NAMES = __load_ac_rnames()

  if parameters.showinfo:
    info()
  elif parameters.tlist:
    for name in list_tables(dirpath=MIXDIR if type(parameters.tlist) is bool else parameters.tlist):
      print(name)
  elif parameters.web:
    port = parameters.run_port
    _debug = (parameters.debug != '')
    private_key_path = 'private_key.pem'
    certificate_path = 'certificate.pem'

    # Запуск Flask с использованием SSL
    web_pcr.run('0.0.0.0', port, debug=_debug, ssl_context=(certificate_path, private_key_path))
  else:
    mix_object, reag_table = mix_prep(parameters, table_src='local')
    mix_render(mix_object, parameters, mode='cli')
    print('Exiting.')

# TODO исправить перезагрузку таблицы - проверить сохранение параметров реакции при перезагрузке
