import sys, os
from array import array
from collections import defaultdict
from JMTTools import *
from JMTROOTTools import *
set_style()

def arr(l):
    return array('d', list(l))

def chomp(line, s):
    global last
    if line.startswith(s):
        last = line.replace(s, '').strip()
        return True
    else:
        return False

class datum:
    def __init__(self, dac_vana, caen_iana, vd, va, vana, vbg, iana):
        self.dac_vana = int(dac_vana)
        self.caen_iana = float(caen_iana)
        self.vd = int(vd)
        self.va = int(va)
        self.vana = int(vana)
        self.vbg = int(vbg)
        self.iana = int(iana)
    def __repr__(self):
        return 'datum(%r)' % ((self.dac_vana, self.caen_iana, self.vd, self.va, self.vana, self.vbg, self.iana))

by_roc = defaultdict(list)

vana = None
roc = None
iread = None
last = ''
block = []

for line in open(sys.argv[1]):
    line = line.strip()
    #print line
    if chomp(line, 'Will set Vana = '):
        vana = int(last)
    elif chomp(line, 'iread: '):
        iread = int(last)
    elif not line.startswith('Selected ROC: ') and chomp(line, 'Selected ROC:'):
        roc = last
        block = []
    elif chomp(line, 'Iana: '):
        assert len(block) == 0
        block.append(float(last))
    else:
        for iRB, RB in enumerate('vd va vana vbg iana'.split()):
            if chomp(line, 'Readback: %s: ReadDigFEDOSDFifo: RocHi: ' % RB):
                assert len(block) == iRB + 1
                hi, lo = last.split(' RocLo: ')
                if hi != lo:
                    assert lo == '0'
                block.append(int(hi))
                if RB == 'iana':
                    by_roc[roc].append(datum(vana, *block))
                break

by_roc = [kv for kv in dict(by_roc).iteritems()]
def _key(x):
    a, b = x[0].split('_ROC')
    return a, int(b)
by_roc.sort(key=_key)

run = 874
out_dir = '/nfshome0/pixelpilot/build/TriDAS/pixel/PixelRun/Runs/Run_0/Run_%i/iana_readback' % run
os.system('mkdir -p %s' % out_dir)

c = ROOT.TCanvas('c', '', 2000, 2000)
c.Divide(4,4)
cache = []
for iroc, (roc, data) in enumerate(by_roc):
    c.cd(iroc % 16 + 1)
    data.sort(key=lambda d: d.dac_vana)
    iana_0 = data[0].iana
    x = arr(d.dac_vana for d in data)
    y = arr(d.iana - iana_0 for d in data)
    e = arr(1 for d in data)
    g = ROOT.TGraphErrors(len(data), x, y, e, e)
    g.SetTitle('%s;Vana (DAC units);Iana (ADC units)' % roc)
    f = ROOT.TF1('f', 'pol1', 25, 200)
    g.Fit(f, 'QR')
    g.Draw('AP')
    c.Update()
    stats = g.GetListOfFunctions().At(1)
    assert stats.GetName() == 'stats'
    stats.SetX1NDC(0.141)
    stats.SetY1NDC(0.646)
    stats.SetX2NDC(0.540)
    stats.SetY2NDC(0.862)
    cache.append((g,f))
    if iroc % 16 == 15:
        c.cd(0)
        c.SaveAs(os.path.join(out_dir, roc.split('_ROC')[0] + '.png'))
    

if 'scp' in sys.argv:
    remote_dir = 'public_html/qwer/iana_readback/%i' % run
    cmd = 'ssh jmt46@lnx201.lns.cornell.edu "mkdir -p %s"' % remote_dir
    print cmd
    os.system(cmd)
    cmd = 'scp -r %s/* jmt46@lnx201.lns.cornell.edu:%s' % (out_dir, remote_dir)
    print cmd
    os.system(cmd)
