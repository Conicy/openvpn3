import os, re

from utils import *

def compile_one_file(parms, srcfile, incdirs):
    if parms['DEBUG']:
        dbg_rel_flags = "/Zi"
    else:
        dbg_rel_flags = "/O2"

    paths = {
        "srcfile" : srcfile,
        "incdirs" : ' '.join([r"/I %s" % (x,) for x in incdirs]),
        "dbg_rel_flags" : dbg_rel_flags,
        }

    vc_cmd(parms, r"cl /c /DNOMINMAX /D_CRT_SECURE_NO_WARNINGS %(incdirs)s /EHsc /MD /W3 %(dbg_rel_flags)s /nologo %(srcfile)s" % paths, arch=os.environ.get("ARCH"))

def build_asio(parms):
    print "**************** ASIO"
    with Cd(build_dir(parms)) as cd:
        with ModEnv('PATH', "%s\\bin;%s" % (parms.get('GIT'), os.environ['PATH'])):
            d = expand('asio', parms['DEP'], parms.get('LIB_VERSIONS'))

def build_polarssl(parms):
    print "**************** PolarSSL"
    with Cd(build_dir(parms)) as cd:
        with ModEnv('PATH', "%s\\bin;%s" % (parms.get('GIT'), os.environ['PATH'])):
            dist = os.path.realpath('polarssl')
            rmtree(dist)
            d = expand('polarssl', parms['DEP'], parms.get('LIB_VERSIONS'))
            if d.endswith("-gpl"):
                d = d[:-4]
            os.rename(d, dist)

            # copy our custom config.h
            cp(os.path.join(parms['OVPN3'], 'core', 'deps', 'polarssl', 'config.h'),
               os.path.join(dist, 'include', 'polarssl', 'config.h'))
            with open(os.path.join(dist, 'include', 'polarssl', 'openvpn-polarssl.h'), 'w') as f:
                f.write("// automatically generated by buildep.py\n#define POLARSSL_SELF_TEST\n")
                #f.write("#define POLARSSL_SSL_SRV_C\n") # needed to build test proto.cpp

            # compile the source files
            os.chdir(os.path.join(dist, "library"))
            obj = []
            for dirpath, dirnames, filenames in os.walk("."):
                for f in filenames:
                    if f.endswith(".c"):
                        compile_one_file(parms, f, (r"..\include",))
                        obj.append(f[:-2]+".obj")
                break

            # collect object files into polarssl.lib
            vc_cmd(parms, r"lib /OUT:polarssl.lib " + ' '.join(obj))

def build_lz4(parms):
    print "**************** LZ4"
    with Cd(build_dir(parms)) as cd:
        with ModEnv('PATH', "%s\\bin;%s" % (parms.get('GIT'), os.environ['PATH'])):
            dist = os.path.realpath('lz4')
            rmtree(dist)
            d = expand('lz4', parms['DEP'], parms.get('LIB_VERSIONS'))
            os.rename(d, dist)
            os.chdir(dist)
            compile_one_file(parms, "lz4.c", ())
            vc_cmd(parms, r"lib /OUT:lz4.lib lz4.obj")

def build_jsoncpp(parms):
    if 'jsoncpp' in parms['LIB_VERSIONS']:
        print "**************** JSONCPP"
        with Cd(build_dir(parms)) as cd:
            with ModEnv('PATH', "%s\\bin;%s" % (parms.get('GIT'), os.environ['PATH'])):
                dist = os.path.realpath('jsoncpp')
                rmtree(dist)
                d = expand('jsoncpp', parms['DEP'], parms.get('LIB_VERSIONS'))
                os.rename(d, dist)
                os.chdir(dist)
                call(["python", "amalgamate.py"])
                os.chdir(os.path.join(dist, "dist"))
                compile_one_file(parms, "jsoncpp.cpp", (".",))
                vc_cmd(parms, r"lib /OUT:jsoncpp.lib jsoncpp.obj")

def build_all(parms):
    wipetree(build_dir(parms))
    build_asio(parms)
    build_polarssl(parms)
    build_lz4(parms)
    build_jsoncpp(parms)

if __name__ == "__main__":
    from parms import PARMS
    build_all(PARMS)
