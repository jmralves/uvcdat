import sys, getopt, os, shutil, string, glob, tempfile, hashlib
from distutils.core import setup

build_dir = os.getcwd()
logdir = os.path.join(build_dir, 'logs').replace(" ","\ ")

# Create logs directory if it does not exits
if not os.path.exists(logdir):
  os.makedirs(logdir)

base_build_dir = os.path.join(build_dir, '..')
os.environ['BUILD_DIR'] = build_dir

current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, '..')
installation_script_dir = os.path.join(src_dir, 'installation')
here = installation_script_dir

sys.path.append(src_dir)
sys.path.append(build_dir)
sys.path.append(installation_script_dir)

control_script_path = os.path.join(installation_script_dir, 'control.py')
execfile(control_script_path, globals(), globals())

global target_prefix
target_prefix = sys.prefix
for i in range(len(sys.argv)):
    a = sys.argv[i]
    if a=='--prefix':
        target_prefix=sys.argv[i+1]
    sp = a.split("--prefix=")
    if len(sp)==2:
        target_prefix=sp[1]
        
try:
    os.makedirs(os.path.join(target_prefix,'bin'))
except Exception,err:
    pass
try:
    os.makedirs(os.path.join(target_prefix,'include'))
except Exception,err:
    pass
try:
    os.makedirs(os.path.join(target_prefix,'lib'))
except Exception,err:
    pass

cdms_include_directory = os.path.join(target_prefix, 'include', 'cdms')
cdms_library_directory = os.path.join(target_prefix, 'lib')

version_file_path = os.path.join(base_build_dir, 'version')
Version = open(version_file_path).read().strip()
version = Version.split(".")
for i in range(len(version)):
    try:
        version[i]=int(version[i])
    except:
        version[i]=version[i].strip()

def norm(path):
    "normalize a path"
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))

def testlib (dir, name):
    "Test if there is a library in a certain directory with basic name."
    if os.path.isfile(os.path.join(dir, 'lib' + name + '.a')): 
        return 1
    if os.path.isfile(os.path.join(dir, 'lib' + name + '.so')): 
        return 1
    if os.path.isfile(os.path.join(dir, 'lib' + name + '.sl')): 
        return 1
    return 0

def configure (configuration_files):
    global action, target_prefix 
    options={}
    execfile(os.path.join(installation_script_dir, 'standard.py'), globals(), options)
    for file in configuration_files:
        print >>sys.stderr, 'Reading configuration:', file
        execfile(os.path.join(src_dir, file), globals(), options)

    # Retrieve action
    action = options['action']
    # Establish libraries and directories for CDUNIF/CDMS
    netcdf_directory = norm(options.get('netcdf_directory',os.environ['EXTERNALS']))
    netcdf_include_directory = norm(options.get('netcdf_include_directory', 
                                           os.path.join(os.environ['EXTERNALS'],'include')))
    
    #hdf5_library_directory = norm(os.path.join(os.environ.get('HDF5LOC',os.path.join(os.environ["EXTERNALS"])), 'lib'))
    cdunif_library_directories = [cdms_library_directory]
    options['CDMS_INCLUDE_DAP']="yes"
##     if options.get('CDMS_INCLUDE_DAP','no')=='yes':
##         netcdf_include_directory=norm(os.path.join(options['CDMS_DAP_DIR'],'include','libnc-dap'))
##         netcdf_library_directory=norm(os.path.join(options['CDMS_DAP_DIR'],'lib'))
##         dap_include=[norm(os.path.join(options['CDMS_DAP_DIR'],'include','libdap'))]
##         dap_lib_dir=[norm(os.path.join(options['CDMS_DAP_DIR'],'lib'))]
## ##         dap_lib=['dap','stdc++','nc-dap','dap','curl','z','ssl','crypto','dl','z','xml2','rx','z']
## ##         if (sys.platform in ['linux2',]):
## ##            dap_lib=['nc-dap','dap','stdc++','curl','z','ssl','xml2']
## ##         elif (sys.platform in ['darwin',]):
## ##            dap_lib=['nc-dap','dap','stdc++','curl','z','ssl','pthread','xml2','z']
##         dap_lib=['nc-dap','dap','stdc++','curl','z','ssl','pthread','xml2']
##         dap_lib = ['stdc++']
##         dap_lib_dir=[]
##         Libs=os.popen(norm(os.path.join(options['CDMS_DAP_DIR'],'bin','ncdap-config'))+' --libs').readlines()
##         Libs+=os.popen(norm(os.path.join(options['CDMS_DAP_DIR'],'bin','dap-config'))+' --client-libs').readlines()
##         for libs in Libs:
##             libs=libs.split()
##             for l in libs:
##                 if l[:2]=='-l':
##                     dap_lib.append(l[2:])
##                 elif l[:2]=='-L'and l[2:] not in dap_lib_dir:
##                     dap_lib_dir.append(l[2:])
##         dap_lib.append("dap")
##         dap_lib.append("xml2")
##         netcdfname='nc-dap'
## ##         print 'daplib:',dap_lib
##     else:
    if 1:
        ## dap_include = [os.path.join(hdf5path,"include"),os.path.join(os.environ['EXTERNALS'],'include')]
        dap_include = []
        Dirs=os.popen('%s --cflags' % os.environ.get("LOCNCCONFIG","nc-config")).readlines()[0]
        for d in Dirs.split():
            if d[:2]=="-I":
                dnm = d[2:]
                if not dnm in dap_include:
                    dap_include.append(dnm)
        dap_lib = ['stdc++']
        dap_lib = []
        dap_lib_dir=[]
        ## Libs=os.popen(norm(os.path.join(os.environ['EXTERNALS'],'bin','nc-config'))+' --libs').readlines()
        Libs=os.popen('%s --libs' % os.environ.get("LOCNCCONFIG","nc-config")).readlines()
        for libs in Libs:
            libs=libs.split()
            for l in libs:
                if l[:2]=='-l':
                    dap_lib.append(l[2:])
                elif l[:2]=='-L'and l[2:] not in dap_lib_dir:
                    if l[-3:]!='lib':
                        l+='/lib'
                    dap_lib_dir.append(l[2:])

##         if enable_netcdf3==True:
##             dap_include=[]
##             dap_lib_dir=[]
##         else:
##             dap_include = [os.path.join(hdf5path,"include"),os.path.join(os.environ['EXTERNALS'],'include')]
##             dap_lib_dir = [os.path.join(hdf5path,"lib"),os.path.join(os.environ['EXTERNALS'],'lib')]
##         if enable_netcdf3 is True:
##             daplib=[]
##         else:
##             dap_lib=['hdf5_hl','hdf5','m','z','dap','nc-dap','dapclient','curl','stdc++','xml2']
##             # for now turn off the dap crap
##             dap_lib=['hdf5_hl','hdf5','m','z']
        netcdfname='netcdf'

    if options.get('CDMS_INCLUDE_HDF','no')=='yes':
        hdf_libraries = ['mfhdf','df','jpeg','z']
        hdf_include=[norm(os.path.join(options['CDMS_HDF_DIR'],'include'))]
        hdf_lib_dir=[norm(os.path.join(options['CDMS_HDF_DIR'],'lib'))]
    else:
        hdf_libraries = []
        hdf_include=[]
        hdf_lib_dir=[]

    grib2_libraries = ["grib2c","png","jasper"]
    ## if netcdf_library_directory not in cdunif_library_directories: 
    ##     cdunif_library_directories.append(netcdf_library_directory)
    cdunif_include_directories = [cdms_include_directory]
    ## if netcdf_include_directory not in cdunif_include_directories: 
    ##     cdunif_include_directories.append(netcdf_include_directory)
                         
        
    if sys.platform == "sunos5":
        cdunif_include_directories.append('/usr/include')

    drs_file = norm(options.get('drs_file', '/usr/local/lib/libdrs.a'))

    # Establish location of X11 include and library directories
    if options['x11include'] or options['x11libdir']:
        if options['x11include']: 
            options['x11include'] = norm(options['x11include'])
        if options['x11libdir']: 
            options['x11libdir'] = norm(options['x11libdir'])
    else:
        for x in x11search:
            if os.path.isdir(x):
                if options['x11include']:
                    options['x11include'].append(os.path.join(x, 'include'))
                    options['x11libdir'].append(os.path.join(x, 'lib'))
                else:
                    options['x11include']=[norm(os.path.join(x, 'include'))]
                    options['x11libdir']=[norm(os.path.join(x, 'lib'))]
        else: 
            for w in x11OSF1lib:
                if testlib(w, 'X11'): 
                    if not options['x11libdir']:
                        options['x11libdir'] = [norm(w),]
                    else:
                        options['x11libdir'].append(norm(w))
            for w in x11OSF1include:
                if os.path.isdir(w): 
                    if not options['x11include']:
                        options['x11include'] = [norm(w),]
                    else:
                        options['x11include'].append(norm(w))
    # Check that we have both set correctly.
    if not (options['x11include'] and \
            options['x11libdir'] 
            ): 
        print >>sys.stderr, """
Failed to find X11 directories. Please see README.txt for instructions.
"""
        print options
        raise SystemExit, 1

    # Write cdat_info.py
    os.chdir(installation_script_dir)
    print 'Version is: ',Version
    f = open(os.path.join(build_dir, 'cdat_info.py'), 'w')
    sys.path.append(build_dir)
    print >> f,"""
Version = '%s'
ping = False
def version():
    return %s
""" % (Version,str(version))
    if options.get('CDMS_INCLUDE_DRS','no') == 'yes':
        print >>f, """
def get_drs_dirs ():
    #import Pyfort, os
    import os
    #c = Pyfort.get_compiler('default')
    drs_dir, junk = os.path.split(drs_file)
    #return c.dirlist + [drs_dir]
    return [drs_dir,]

def get_drs_libs ():
    #import Pyfort
    #c = Pyfort.get_compiler('default')
    return ['drs',] + %s
""" % repr(options.get("COMPILER_EXTRA_LIBS",[]))
    else:
        print >>f, """
def get_drs_dirs ():
    return []
def get_drs_libs():
    return []
"""

    print >>f, """\
ping=True

sleep=60 #minutes  (int required)

actions_sent = {}

SOURCE = 'CDAT'

def get_version():
  return '1.3.0'

def pingPCMDIdb(*args,**kargs):
    import threading
    kargs['target']=submitPing
    kargs['args']=args
    t = threading.Thread(**kargs)
    t.start()
    
def submitPing(source,action,source_version=None):
  try:
    import urllib2,sys,os,cdat_info,hashlib,urllib
    if source in ['cdat','auto',None]:
      source = cdat_info.SOURCE
    if cdat_info.ping:
      if not source in actions_sent.keys():
        actions_sent[source]=[]
      elif action in actions_sent[source]:
        return
      else:
        actions_sent[source].append(action)
      data={}
      uname = os.uname()
      data['platform']=uname[0]
      data['platform_version']=uname[2]
      data['hashed_hostname']=hashlib.sha1(uname[1]).hexdigest()
      data['source']=source
      if source_version is None:
        data['source_version']=cdat_info.get_version()
      else:
        data['source_version']=source_version
      data['action']=action
      data['sleep']=cdat_info.sleep
      data['hashed_username']=hashlib.sha1(os.getlogin()).hexdigest()
      urllib2.urlopen('http://uv-cdat.llnl.gov/UVCDATUsage/log/add/',urllib.urlencode(data))
  except Exception,err:
    pass

CDMS_INCLUDE_DAP = %s
CDMS_DAP_DIR = %s
CDMS_HDF_DIR = %s
CDMS_GRIB2LIB_DIR = %s
CDMS_INCLUDE_GRIB2LIB = %s
CDMS_INCLUDE_DRS = %s
CDMS_INCLUDE_HDF = %s
CDMS_INCLUDE_PP = %s
CDMS_INCLUDE_QL = %s
drs_file = %s
netcdf_directory = %s
netcdf_include_directory = %s
cdunif_include_directories = %s + %s + %s
cdunif_library_directories = %s + get_drs_dirs() + %s +%s
cdunif_libraries = %s + %s + get_drs_libs() + %s + %s
x11include = %s
x11libdir = %s
mathlibs = %s
action = %s
externals = %s
""" % ( 
        repr(options.get('CDMS_INCLUDE_DAP','no')),
        repr(options.get('CDMS_DAP_DIR','.')),
        repr(options.get('CDMS_HDF_DIR','.')),
        repr(options.get('CDMS_GRIB2LIB_DIR',os.environ['EXTERNALS'])),
        repr(options.get('CDMS_INCLUDE_GRIB2LIB',"yes")),
        repr(options['CDMS_INCLUDE_DRS']),
        repr(options['CDMS_INCLUDE_HDF']),
        repr(options['CDMS_INCLUDE_PP']),
        repr(options['CDMS_INCLUDE_QL']),
        repr(drs_file),
        repr(netcdf_directory),
        repr(netcdf_include_directory),
        repr(cdunif_include_directories),repr(dap_include),repr(hdf_include),
        repr(cdunif_library_directories),repr(dap_lib_dir),repr(hdf_lib_dir),
        repr(['cdms', netcdfname]),repr(dap_lib),repr(hdf_libraries),repr(grib2_libraries),
        repr(options['x11include']),
        repr(options['x11libdir']),
        repr(options['mathlibs']),
        repr(options['action']),
        repr(os.environ['EXTERNALS']),
        )
    if enable_aqua:
	print >> f,'enable_aqua = True'
    else:
        print >>f, 'enable_aqua = False'
    f.close()
    cdat_info_path = os.path.join(os.environ['BUILD_DIR'], 'cdat_info')
    if not norun: 
      # Install the configuration
      #would be best to add 'clean' but it gives stupid warning error
      sys.argv[1:]=['-q', 'install', '--prefix=%s' % target_prefix]
      setup (name="cdat_info",
       version="0.0",
       py_modules=[cdat_info_path]
      )
      os.system('/bin/rm -fr build')
    
    py_prefix = os.path.join(target_prefix,'lib','python%i.%i' % sys.version_info[:2],'site-packages')
    cdat_info_src_path = os.path.join(build_dir, 'cdat_info.py')
    cdat_info_dst_path = os.path.join(py_prefix, 'cdat_info.py')
    if os.path.isfile(cdat_info_src_path):
        shutil.copyfile(cdat_info_src_path, cdat_info_dst_path)
    else:
       print>>sys.stderr, 'Failed to copy %s to %s' % (cdat_info_src_path, cdat_info_dst_path)        
    
    os.chdir(here)
    print >>sys.stderr, 'Configuration installed.'

def usage():
    f = open('HELP.txt')
    lines = f.readlines()
    f.close()
    for line in lines[10:-9]:
        sys.stdout.write(line)
    print '\tDefault Packages'
    print '\t----------------'
    packages.append('\n\tContributed Packages\n\t--------------------')
    #execfile('installation/contrib.py',globals(),globals())
    for p in packages:
        print '\t\t',p

def main(arglist):
    global norun, echo, force, do_configure, silent, action, logdir, enable_aqua,target_prefix, enable_netcdf3, hdf5path,zpath
    enable_aqua = False
    enable_cdms1 = False
    enable_netcdf3=False
    optlist, control_names = getopt.getopt(arglist, 
                       "c:defhnPl", 
                       ["enable-cdms-only",
                        "configuration=", 
                        "debug",
                        "prefix=",
                        "echo",
                        "force", 
                        "help",
                        "with-externals=",
                        "norun",
                        "PCMDI",
                        "pcmdi",
                        "psql","enable-psql",
                        "enable-hdf4","enable-HDF4",
                        "with-HDF4=","with-hdf4=",
                        "disable-hdf4","disable-HDF4",
                        "disable-contrib",
                        "enable-pp",
                        "disable-externals-build",
                        "disable-pp",
                        ## Bellow are the arguments that could be passed to exsrc, nothing done with them
                        "disable-R","disable-r",
                        #"disable-VTK","disable-vtk",
                        "disable-XGKS","disable-xgks",
                        "disable-Pyfort","disable-pyfort",
                        "disable-NetCDF","disable-netcdf","disable-NETCDF",
                        "disable-Numeric","disable-numeric",
                        "disable-gplot","disable-GPLOT","disable-Gplot",
                        "disable-gifsicle","disable-GIFSICLE",
                        "disable-gifmerge","disable-GIFMERGE",
                        "disable-pbmplus","disable-PBMPLUS",
                        "disable-netpbm","disable-NETPBM",
                        "disable-Pmw","disable-pmw",
                        "disable-ioapi",
                        "disable-cairo",
                        "disable-ffmpeg",
                        "disable-freetype",
                        "disable-sampledata",
                        "enable-ioapi",
                        "enable-R","enable-r",
                        "enable-numpy","disable-numpy",
                        "enable-scipy","disable-scipy",
                        "enable-ipython","disable-ipython",
                        #"enable-VTK","enable-vtk",
                        "enable-XGKS","enable-xgks",
                        "enable-Pyfort","enable-pyfort",
                        "enable-NetCDF","enable-netcdf","enable-NETCDF","enable-netcdf-fortran","enable-NETCDF-Fortran",
                        "enable-Numeric","enable-numeric",
                        "enable-gplot","enable-GPlot","enable-GPLOT",
                        "enable-gifsicle","enable-GIFSICLE",
                        "enable-gifmerge","enable-GIFMERGE",
                        "enable-pbmplus","enable-PBMPLUS",
                        "enable-netpbm","enable-NETPBM",
                        "enable-Pmw","enable-pmw",
                        "enable-aqua","enable-Aqua","enable-AQUA",
                        "enable-cairo",
                        "enable-ffmpeg",
                        "enable-freetype",
                        "enable-cdms1",
                        "enable-netcdf3",
                        "enable-spanlib",
                        "disable-spanlib"
                        "disable-tkbuild",
                        "enable-qt",
                        "enable-qt-framework",
                        "with-qt=",
                        "with-qt-lib=",
                        "with-qt-inc=",
                        "with-qt-bin=",
                        "qt-debug",
                        "list",
                       ]
                    )
    configuration_files = []
    nodap=0
    nopp=0
    nohdf=0
    selfhdf=0
    selfdap=0
    selfpp=0
    showlist=0
    qtfw=False
    qtinc=None
    qtlib=None
    qtbin=None
    qt=False
    control_names = ['contrib']
    sampleData = True
##     prefix_target = sys.exec_prefix
    externals = os.environ.get("EXTERNALS",os.path.join(sys.prefix,"Externals"))
    hdf5path = None
    zpath = None
    
    for i in range(len(optlist)):
        letter=optlist[i][0]
        if letter == "--enable-qt":
            qt=True
        if letter == "--enable-qt-framework":
            qtfw=True
        if letter == "--with-qt":
            qtinc=os.path.join(optlist[i][1],"include")
            qtlib=os.path.join(optlist[i][1],"lib")
            qtbin=os.path.join(optlist[i][1],"bin")
        if letter == "--with-qt-inc":
            qtinc=optlist[i][1]
        if letter == "--with-qt-bin":
            qtbin=optlist[i][1]
        if letter == "--with-qt-lib":
            qtlib=optlist[i][1]
        if letter == "--enable-cdms-only":
            control_names = ['cdmsonly']+control_names
            if 'contrib' in control_names:
                control_names.pop(control_names.index('contrib'))
        elif letter == "--with-externals":
            externals = optlist[i][1]
        elif letter in ["-c",  "--configuration"]:
            m = False
            n = optlist[i][1]
            if os.path.isfile(n):
                m = n
            elif os.path.isfile(n + '.py'):
                m = n + '.py'
            elif os.path.isfile(os.path.join('installation', n)):
                m = os.path.join('installation', n)
            elif os.path.isfile(os.path.join('installation', n + '.py')):
                m = os.path.join('installation', n + '.py')
            if m:
                configuration_files.append(m)
            else:
                print >>sys.stderr, "Cannot find configuration file", optlist[i][1]
            force = 1
            do_configure = 1
        elif letter in ["-d", "--debug"]:
            debug_file = os.path.join('installation','debug.py')
            configuration_files.append(debug_file)   
            force = 1
            do_configure = 1
        elif letter in ["-e", "--echo"]:
            echo = 1
        elif letter in ["--enable-cdms1"]:
            enable_cdms1 = True
        elif letter in ["--enable-netcdf3"]:
            enable_netcdf3 = True
	elif letter in ["--enable-aqua","--enable-Aqua","--enable-AQUA"]:
	    enable_aqua = True
        elif letter in ["-f", "--force"]:
            force = 1
            do_configure = 1
        elif letter in ["-h", "--help"]:
            usage()
            raise SystemExit, 1
        elif letter in ["-P", "--PCMDI", "--pcmdi"]:
            configuration_files.append(os.path.join('installation', 'pcmdi.py'))
            force=1
            do_configure=1  # Need libcdms built a certain way too.
        elif letter in ["--psql", "--enable-psql"]:
            configuration_files.append(os.path.join('installation', 'psql.py'))
            do_configure=1  # Need libcdms built a certain way too.
##         elif letter in ["--with-OpenDAP", "--with-opendap", "--with-OPENDAP","--enable-opendap","--enable-OpenDAP","--enable-OPENDAP"]:
##             configuration_files.append(os.path.join('installation', 'DAP.py'))
##             do_configure=1  # Need libcdms built a certain way too.
##             selfdap=1
##         elif letter in ["--with-HDF4", "--with-hdf4",'--enable-hdf4','--enable-HDF4']:
##             configuration_files.append(os.path.join('installation', 'HDF.py'))
##             do_configure=1  # Need libcdms built a certain way too.
##             selfhdf=1
        elif letter in ["--with-hdf5",]:
            hdf5path = optlist[i][1]
        elif letter in ["--with-z",]:
            zpath = optlist[i][1]
        elif letter in ["--prefix"]:
            target_prefix = optlist[i][1]
        elif letter in ['--enable-pp','--enable-PP']:
            configuration_files.append(os.path.join('installation', 'pp.py'))
            do_configure=1  # Need libcdms built a certain way too.
            selfpp=1
##         elif letter in ["--enable-NetCDF","--enable-NETCDF","--enable-netcdf",
##                         "--enable-netcdf-fortran",
##                         "--disable-opendap","--disable-OpenDAP","--disable-OPENDAP"]:
##             nodap=1
##         elif letter in ["--disable-hdf4","--disable-HDF4"]:
##             nohdf=1
        elif letter in ["--disable-pp","--disable-PP"]:
            nohdf=1
        elif letter in ["--disable-sampledata",]:
            sampleData = False
        elif letter in ["-n", "--norun"]:
            norun = 1
        elif letter in ['--list','-l']:
            showlist=1
        elif letter in ['--disable-contrib']:
            for i in range(len(control_names)):
                if control_names[i]=='contrib':
                    control_names.pop(i)
                    i=i-1
    CDMS_INCLUDE_DAP='yes'
    if nopp==1 and selfpp==1:
        raise "Error you chose to both enable and disable PP support !"
    if nohdf==1 and selfhdf==1:
        raise "Error you chose to both enable and disable HDF !"
##     if (nodap==0 and selfdap==0) and (sys.platform in ['linux2','darwin']):
##         configuration_files.append(os.path.join('installation', 'DAP.py'))
##         do_configure=1  # Need libcdms built a certain way too.
##     if (nohdf==0 and selfhdf==0) and (sys.platform in ['linux2','darwin']):
##         configuration_files.append(os.path.join('installation', 'HDF.py'))
##         do_configure=1  # Need libcdms built a certain way too.
    if (nopp==0 and selfpp==0) and (sys.platform in ['linux2','darwin']):
        configuration_files.append(os.path.join('installation', 'pp.py'))
        do_configure=1  # Need libcdms built a certain way too.

    if hdf5path is None: hdf5path= os.path.join(externals)
    if zpath is None: zpath= externals
    os.environ['EXTERNALS']=externals

    control_files = []
    for n in control_names:
        m = ''
        if os.path.isfile(n):
            m = n
        elif os.path.isfile(n + '.py'):
            m = n + '.py'
        elif os.path.isfile(os.path.join('installation', n)):
            m = os.path.join('installation', n)
        elif os.path.isfile(os.path.join('installation', n + '.py')):
            m = os.path.join('installation', n + '.py')
        elif os.path.isfile(os.path.join(src_dir, 'installation', n + '.py')):
            m = os.path.join(src_dir, 'installation', n + '.py')

        if m:
            control_files.append(m)
        else:
            print >>sys.stderr, 'Cannot find control file', n
            raise SystemExit, 1

    for control_file in control_files:
        print 'Running:',control_file
        execfile(control_file, globals(), globals())

    if showlist:
        print 'List of Packages that would be installed:'
        for p in packages:
            print p
        sys.exit()
    if force:
        os.system('./scripts/clean_script')

    sys.path.insert(0,os.path.join(target_prefix,'lib','python%i.%i' % sys.version_info[:2],'site-packages'))
    if do_configure:
        force = 1
        if os.path.isfile(os.path.join(build_dir, 'cdat_info.py')):
            os.unlink(os.path.join(build_dir, 'cdat_info.py'))
        print >>sys.stderr, 'Configuring & installing scripts.'
        configure(configuration_files)
        images_path = os.path.join(src_dir, 'images')
        os.chdir(images_path)
        scripts = glob.glob('*')
        for script in scripts:
            if script[-1] == '~': continue
            if script == "README.txt": continue
            target = os.path.join(target_prefix, 'bin', script)
            if os.path.isfile(target): os.unlink(target)
            shutil.copy(script, target)
        os.chdir(here)
        dat_dir = os.path.join(src_dir, 'Packages/dat')
        os.chdir(dat_dir)
        target = os.path.join(target_prefix, 'sample_data')
        command = 'grep wget %s/checked_get.sh' % os.path.join(os.environ['BUILD_DIR'], "..")
        command = command + ' | tr -s " " | cut -d " " -f 2'
        wget = os.popen(command).readlines()[0].strip()
        data_source_url = "http://uv-cdat.llnl.gov/cdat/sample_data"
        dfiles=open("files.txt")
        data_files=dfiles.readlines()
        dfiles.close()
        try:
            os.makedirs(target)
        except:
            pass
        if sampleData: # Turn to False to skip sample_data download, need to add an option to turn this off
            for df in data_files:
                sp=df.strip().split()
                fnm=sp[1]
                target = os.path.join(target_prefix, 'sample_data', fnm)
                md5=''
                tries=0
                if os.path.exists(target) :
                    data_files=open(target)
                    t=data_files.read()
                    data_files.close()
                    md5=hashlib.md5(t)
                    md5=md5.hexdigest()
                while md5 != sp[0] and tries<5:
                    print 'Redownloading target: %s' % fnm
                    print 'target: ', target
                    print 'data_source_url', data_source_url
                    print 'fnm', fnm
                    ln = os.popen("%s -O %s %s/%s" % (wget,target,data_source_url,fnm)).readlines()
                    tries+=1
                    data_files=open(target)
                    t=data_files.read()
                    data_files.close()
                    md5=hashlib.md5(t)
                    md5=md5.hexdigest()
                if md5!=sp[0]:
                    print 'Error downloading:',fnm
        os.chdir(here)
    else:
        import cdat_info
        action = cdat_info.action

    # Install CDMS
    cdms_library_file = os.path.join(cdms_library_directory, 'libcdms.a')
    if force or not os.path.isfile(cdms_library_file):
        install('libcdms', action)
        if (sys.platform in ['darwin',]):
           os.system('ranlib '+os.path.join(target_prefix,'lib','libcdms.a'))

    # Install Packages
    package_errors=0
    package_failed=[]
    if enable_cdms1:
        packages.append("Packages/regrid")
        packages.append("Packages/cdms")
    for p in packages:
        h = os.getcwd()
        oldcmd=action["setup.py"]+""
        action['setup.py'] = action['setup.py'].strip()[:-1]+" build -b "+ os.environ['BUILD_DIR']+"/"+p
        try:
            if p == "Packages/vcs":
                if qtfw:
                    action["setup.py"]=oldcmd.strip()[:-1]+" --enable-qt-framework ; "
                if qt:
                    action["setup.py"]=oldcmd.strip()[:-1]+" --enable-qt ; "
                if qtinc is not None:
                    action["setup.py"]=action["setup.py"].strip()[:-1]+" --with-qt-inc=%s ; "%qtinc
                if qtlib is not None:
                    action["setup.py"]=action["setup.py"].strip()[:-1]+" --with-qt-lib=%s ; "%qtlib
                if qtbin is not None:
                    action["setup.py"]=action["setup.py"].strip()[:-1]+" --with-qt-bin=%s ; "%qtbin
            install(p, action)
        except:
            package_errors+=1
            package_failed.append(p)
            os.chdir(h)
            print >>sys.stderr, 'Error: Installation of Package:',p,'FAILED'
        action["setup.py"]=oldcmd

    # Celebrate
    if echo:
        print "Simulated build complete."
    elif not silent:
        print >>sys.stderr, finish
        if package_errors!=0:
            print >>sys.stderr, '\n              --- WARNING ---\n'
            print >>sys.stderr,package_errors,'Packages reported as FAILED, see logs\n'
            for p in package_failed:
                print >>sys.stderr,'\t\t',p
            print >>sys.stderr
        print >>sys.stderr, '******************************************************\n'
        """
        ******************************************************
        CDAT has been installed in %s .
        Please make sure all modules built successfully
        (see above build messages)
        ******************************************************
        """ %(target_prefix,)

def _install(file, action):
    h = os.getcwd()
    absfile = os.path.abspath(file)
    print 'absfile ', absfile
    dirname, basename = os.path.split(absfile)
    dirfinal = os.path.split(dirname)[-1]
    os.chdir(dirname)
    name, ext = os.path.splitext(basename)
    if ext.lower() == ".pfp":
        p1 = action['*.pfp']
    elif action.has_key(absfile):
        p1 = action[absfile]
    elif action.has_key(file):
        p1 = action[file]
    elif action.has_key(basename):
        p1 = action[basename]
    else:
        print "Do not know what to do with", file, "in", dirname
        print >>sys.stderr, "Do not know what to do with", file, "in", dirname
        raise SystemExit, 1

    if log:
        logfile = os.path.join(logdir, dirfinal+".LOG")
        if not silent:
            print >>sys.stderr, "Processing", dirfinal + ', log =', logfile
    else:
        logfile = tempfile.mktemp()
        if not silent:
            print >>sys.stderr, "Processing", dirfinal
    p1 = p1 % { 'filename': file }
    sep = " > %s 2>&1 ; " % logfile
    p = sep.join(p1.split(";"))
##     os.environ["CFLAGS"]="%s -L%s/lib" % (os.environ.get("CFLAGS",""), os.environ["EXTERNALS"])
    add_lib = "-L%s/lib" % (os.environ["EXTERNALS"],)
    cflags_current = os.environ.get("CFLAGS","")
    if cflags_current.find(add_lib) == -1:
        os.environ["CFLAGS"]="%s %s" % (cflags_current, add_lib)
    p = 'env CFLAGS="%s" %s' % (os.environ["CFLAGS"],p)
    if echo:
        print >> sys.stderr, p
    print norun
    if norun:
        r = 0
    else:
        #print '====>executing: ', p
        r = os.system(p)
    if r:
        print >>sys.stderr, "Install failed in directory", dirname
        print >>sys.stderr, "Log=", logfile
        raise SystemExit, 1
    elif not log and not norun:
        os.unlink(logfile)
    
    f = open(os.path.join(build_dir, 'rebuild.py'), 'w')
    print >>f, """
import os
j = os.system(%s)
if j:
    print 'Compilation failed'
    raise SystemExit, 1
""" % (repr(p1+ " 1>LOG.rebuild"),)
    f.close()
    os.chdir(h)

def install (arg, action):
    arg = os.path.normpath(arg)
    installer = ''
    arg = os.path.join(src_dir, arg)
    if os.path.isdir(arg):
        for x in (glob.glob(os.path.join(arg, '*.pfp')) + \
                 ['autogen.sh',
                  'install.py', 
                  'setup.py', 
                  'install_script',
                  'Makefile',
                  'makefile'] ):
            name = os.path.join(arg,x)
            if os.path.isfile(name):
                installer = name
                break
        else:
            print >>sys.stderr, "Cannot find installation instructions in", arg
            raise SystemExit, 1
    elif os.path.isfile(arg):
        installer = arg
        designator, junk = os.path.split(arg)
    else:
        print >>sys.stderr, "Cannot find", arg
        raise SystemExit

    _install(installer, action)


if __name__ == "__main__":
    arglist = sys.argv[1:]
    main(arglist)
    ## This parts creates links from Externals...
    try:
        import cdat_info
        externals = cdat_info.externals
    except:
        externals = os.path.join(sys.prefix,"Externals")
    externals = os.environ.get("EXTERNALS",externals)
    externals_path = os.path.join(externals,'bin')
    files = os.listdir(externals_path)
    for file in files:
        fnm = os.path.join(sys.prefix,'bin',file)
        if not os.path.exists(fnm) and not os.path.islink(fnm):
            try:
                os.symlink(os.path.join(externals_path,file),fnm)
            except:
                pass
 
