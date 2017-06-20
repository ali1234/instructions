#!/usr/bin/env python

import tempfile
import subprocess
import errno
import os
import sys
import collections

LDRAW_DIR='/usr/share/ldraw'
LGEO_DIR='/home/al/lgeo'
L3P_BIN='l3p'
POV_BIN='povray'
LEOCAD_BIN='/home/al/leocad/build/release/leocad'


def render_ldraw_pov(ldrfile, outfile, width=400, height=300, l3p_args=[], pov_args=[]):
    with tempfile.NamedTemporaryFile(suffix='.pov') as povfile:

        subprocess.check_call([L3P_BIN, '-o', '-car'+str((1.0*width)/height),
                               '-bu', '-illights.inc', '-ldd'+LDRAW_DIR, '-lgd'+LGEO_DIR,
                               '-lgeo'] + l3p_args + [ldrfile, povfile.name])

        subprocess.check_call([POV_BIN, '-L'+LGEO_DIR+'/lg', '-L'+LGEO_DIR+'/ar',
                               '-W'+str(width), '-H'+str(height), '+A0.3',
                               '+R4'] + pov_args + ['-O'+outfile, povfile.name])

def render_ldraw_leocad(ldrfile, outfile, width=400, height=300, leocad_args=[]):

    subprocess.check_call([LEOCAD_BIN, '-i', outfile,
                           '-w', str(width), '-h', str(height)] + leocad_args + [ldrfile])

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class Part(object):
    def __init__(self, part, colour, transformation='0 0 0 1 0 0 0 1 0 0 0 1', suffix='.DAT'):
        self.part = str(part)
        self.colour = colour
        self.transformation = transformation
        self.suffix = suffix

    def tostring(self):
        return ' '.join(['1', str(self.colour), self.transformation, self.part+self.suffix])

    def filename(self):
        return self.part+self.suffix

    def imgname(self):
        return self.part+'-'+str(self.colour)+'.png'

    def render(self, outdir, width=2560, height=1280, renderer='leocad', camerapos=(600,-1200,600)):
        """Render an image of a single part, using leocad or l3p and pov.
           
           pov coords: x, -z, -y
           leocad coords: x, y, z"""

        with tempfile.NamedTemporaryFile(suffix='.ldr') as ldrfile:
            ldrfile.write(self.tostring()+'\n')
            ldrfile.flush()
            if renderer == 'pov':
                render_ldraw_pov(ldrfile.name, outdir+self.imgname(), width, height,
                                 l3p_args=['-cc%f,%f,%f' % (camerapos[0], -camerapos[2], camerapos[1]),
                                           '-cla0.0,0.0,0.0', '-ca19.89', '-q4'],
                                 pov_args=['-d', '-Q11', '+ua'])

            elif renderer == 'leocad':
                ldrfile.write(Camera(fov=10).tostring())
                ldrfile.flush()

                render_ldraw_leocad(ldrfile.name, outdir+self.imgname(), width, height,
                                    leocad_args=['-c', 'camera', '-f', '2'])

            subprocess.check_call(['mogrify', '-trim', '+repage', outdir+self.imgname()])

    @classmethod
    def part_test(self, part='3298p90', colour=7):
        mkdir_p('parttest')
        Part(str(part), str(colour)).render('parttest/p', renderer='pov')
        Part(str(part), str(colour)).render('parttest/l', renderer='leocad')
        exit(0)

class Step(object):
    def __init__(self):
        self.parts = []

    def add_part(self, part):
        self.parts.append(part)

    def unique_parts(self, ignore=[]):
        pset = set()
        for p in self.parts:
            if p.part.upper() not in ignore:
                pset.add((p.part, p.colour))
        return pset

    def num_parts(self, ignore=[]):
        c = collections.Counter()
        for p in self.parts:
            if p.part.upper() not in ignore:
                c.update({(p.part, p.colour): 1})
        return c

    def tostring(self):
        str = '\n'.join([p.tostring() for p in self.parts])
        if len(str):
            str += '\n'
        return str

class Camera(object):
    def __init__(self, name='camera', eye=(600,-1200,600), look=(0, 0, 0), up=(0, 0, 1), fov=30):
        self.name = name
        self.eye = eye
        self.look = look
        self.up = up
        self.fov = fov

    def set_eye(self, x, y, z):
        self.eye = (x, y, z)

    def set_look(self, x, y, z):
        self.look = (x, y, z)

    def set_up(self, x, y, z):
        self.up = (x, y, z)

    def to_pov(self, v):
        return (v[0], -v[2], v[1])

    def get_eye_pov(self):
        return self.to_pov(self.eye)

    def get_look_pov(self):
        return self.to_pov(self.look)

    def get_up_pov(self):
        return self.to_pov(self.up)

    def get_fov_pov(self):
        return self.fov * 1.5

    def tostring(self):
        return ''.join([
            '0 !LEOCAD CAMERA FOV %d ZNEAR 25 ZFAR 50000\n' % (self.fov),
            '0 !LEOCAD CAMERA POSITION_KEY 1 %f %f %f\n' % (self.eye),
            '0 !LEOCAD CAMERA TARGET_POSITION_KEY 1 %f %f %f\n' % (self.look),
            '0 !LEOCAD CAMERA UP_VECTOR_KEY 1 %f %f %f\n' % (self.up),
            '0 !LEOCAD CAMERA NAME %s\n' % (self.name)
        ])


class Model(object):
    def __init__(self, name, suffix):
        self.name = name
        self.suffix = suffix
        self.steps = []
        self.submodels = []
        self.cameras = {}
        self.add_step()

    def add_step(self):
        self.steps.append(Step())
        self.current_step = self.steps[-1]

    def add_part(self, part):
        self.current_step.add_part(part)

    def add_submodel(self, model):
        self.submodels[model.name + model.suffix] = model

    def unique_parts(self, ignore=[]):
        return set.union(*[s.unique_parts(ignore) for s in self.steps])

    def num_parts(self, ignore=[]):
        c = collections.Counter()
        for counts in [s.num_parts(ignore) for s in self.steps]:
            c.update(counts)
        return c

    def tostring(self):
        return '\n'.join(['0 FILE '+self.name+self.suffix,
                          '0 STEP\n'.join([s.tostring() for s in self.steps]),
                          '0 NOFILE'])

    def imgname(self):
        return self.name + '-' + ('0' if (len(self.steps)+1) < 10 else '') + '.png'

    def render_steps_pov(self, outdir, width=2000, height=1500):
        """This is broken."""
        with tempfile.NamedTemporaryFile(suffix='.inc') as camfile:
            with tempfile.NamedTemporaryFile(suffix='.ldr') as ldrfile:
                ldrfile.write(self.tostring() + '\n')
                for m in self.submodels:
                    ldrfile.write(m.tostring() + '\n')
                ldrfile.flush()
                nsteps = (len(self.steps)+1)
                render_ldraw_pov(ldrfile.name, outdir+self.imgname(), width, height,
                                 l3p_args=['-sw2.0', '-ca30', '-scm', '-q4'], # -iccamfile
                                 pov_args=['-Q11', '+ua',
                                           '+FN', '+KI1', '+KFI1',
                                           '+KF'+str(nsteps),
                                           '+KFF'+str(nsteps),
                                           '+A'])


class Project(object):
    def __init__(self, filename):
        self.filename = filename
        self.models = []
        self.model_dict = {}
        current_model = None   

        with open(filename) as data:
            for line in data:
                x = line.strip().split()
                if x[0] == '0':
                    if x[1] == 'FILE':
                        self.models.append(Model(x[2][:-4], x[2][-4:]))
                        current_model = self.models[-1]
                        self.model_dict[current_model.name.upper()] = current_model
                    elif x[1] == 'NOFILE':
                        current_model = None
                    elif x[1] == 'STEP':
                        current_model.add_step()
                    elif x[1] == '!LEOCAD' and x[2] == 'CAMERA':
                        if x[3] == 'FOV':
                            current_camera = Camera(float(x[4]))
                        elif x[3] == ('POSITION'):
                            current_camera.set_eye(float(x[4]), float(x[5]), float(x[6]))
                        elif x[3] == ('TARGET_POSITION'):
                            current_camera.set_look(float(x[4]), float(x[5]), float(x[6]))
                        elif x[3] == ('UP_VECTOR'):
                            current_camera.set_up(float(x[4]), float(x[5]), float(x[6]))
                        elif x[3] == ('POSITION_KEY'):
                            current_camera.set_eye(float(x[5]), float(x[6]), float(x[7]))
                        elif x[3] == ('TARGET_POSITION_KEY'):
                            current_camera.set_look(float(x[5]), float(x[6]), float(x[7]))
                        elif x[3] == ('UP_VECTOR_KEY'):
                            current_camera.set_up(float(x[5]), float(x[6]), float(x[7]))
                        elif x[3] == 'NAME':
                            current_model.cameras[x[4]] = current_camera
                elif x[0] == '1':
                    colour = x[1]
                    part = x[-1][:-4]
                    transformation = ' '.join(x[2:-1])
                    suffix = x[-1][-4:]
                    current_model.add_part(Part(part, colour, transformation, suffix))

        self.model_names = [m.name.upper() for m in self.models]        
                    
    def render_parts(self, outdir, ignore=['3811', '4187']):
        mkdir_p(outdir+'/parts/')
        unique_parts = set.union(*[m.unique_parts(ignore=ignore+self.model_names) for m in self.models])
        print 'Rendering', len(unique_parts), 'part images',
        for part,colour in unique_parts:
            sys.stdout.write('.')
            sys.stdout.flush()
            Part(part, colour).render(outdir+'/parts/')
        print ' done.'

    def render_steps(self, outdir):
        mkdir_p(outdir+'/steps/')
        for m in self.models:
            print 'Rendering submodel', m.name, '-', len(m.steps), 'steps.'
            render_ldraw_leocad(self.filename, outdir+'/steps/'+m.name+'-.png', 4000, 3000,
                                leocad_args=['-m', m.name+m.suffix, '-c', 'step_camera',
                                             '-f', '1', '-t', str(len(m.steps)+1)])

    def model_steps(self, model):
        self.stepped.append(model)
        for sn,s in enumerate(model.steps):
            for p in s.parts:
                name = p.part.upper()
                if name in self.model_names and self.model_dict[name] not in self.stepped:
                    for x in self.model_steps(self.model_dict[name]):
                        yield x
            yield sn,model,s


    def steps(self):
        self.stepped = []
        for x in self.model_steps(self.models[0]):
            yield x

    def render_extra(self, outdir, width=4000, height=4000):
        mkdir_p(outdir+'/renders/')
        for name,camera in self.models[0].cameras.iteritems():
            render_ldraw_pov(self.filename, outdir+'/renders/'+name+'.png', width, height,
                                 l3p_args=['-cc%f,%f,%f' % camera.get_eye_pov(),
                                           '-cla%f,%f,%f' % camera.get_look_pov(),
                                           '-ca%f' % camera.get_fov_pov(), '-b', '-f', '-q4'],
                                 pov_args=['-Q11'])

    def generate_html(self, outdir, ignore=['3811', '4187']):
        with open(outdir+'/index.html', 'w') as html:
            html.write('<html>\n<head>\n')
            html.write(' <link rel="stylesheet" href="../style.css">\n')
            html.write(' <script src="../image-dpi.js"></script>\n')
            html.write('</head>\n<body onload="resize_images();">\n')
            for sn,m,s in self.steps():
                if len(s.unique_parts(ignore=ignore)) == 0:
                    continue
                print sn, m.name
                html.write('<div class="step">\n')
                html.write('  <div class="stepnum"></div>\n')
                html.write('  <img class="stepimg" src="steps/'+m.name+('-%02d.png'%(sn+1))+'" />\n')
                html.write('  <ul class="partslist">\n')
                parts = s.num_parts(ignore=ignore+self.model_names)
                for p in parts:
                    html.write('    <li><img src="parts/'+Part(p[0], p[1]).imgname()+'" /> x'+str(parts[p])+'</li>\n')
                html.write('  </ul>\n')
                html.write('</div>\n')
            html.write('\n</body>\n</html>\n')


if __name__ == '__main__':
    p = Project(sys.argv[1])
    p.render_parts(sys.argv[2])
    p.render_steps(sys.argv[2])
    p.generate_html(sys.argv[2])
    p.render_extra(sys.argv[2])

