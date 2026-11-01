#!/usr/bin/env python3
"""Package one verified ESP32-C3 build; never access or write a device."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def partitions(path):
    raw=path.read_bytes();result=[]
    for at in range(0,len(raw),32):
        entry=raw[at:at+32]
        if len(entry)<32:raise ValueError('truncated partition entry')
        magic=struct.unpack_from('<H',entry)[0]
        if magic==0xffff:break
        if magic==0xebeb:
            if entry[16:]!=hashlib.md5(raw[:at]).digest():raise ValueError('partition MD5 mismatch')
            break
        if magic!=0x50aa:raise ValueError('invalid partition magic')
        _,kind,subtype,offset,size,label,flags=struct.unpack('<HBBII16sI',entry)
        name=label.split(b'\0',1)[0].decode('ascii')
        if offset+size>0x800000:raise ValueError('partition exceeds 8 MB')
        if any(offset<p['offset']+p['size'] and p['offset']<offset+size for p in result):raise ValueError('overlapping partitions')
        result.append(dict(name=name,type=kind,subtype=subtype,offset=offset,size=size,flags=flags))
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,default=ROOT/'firmware/passport_device/build');args=parser.parse_args()
    build=args.build.resolve();config=json.loads((build/'config/sdkconfig.json').read_text())
    if config.get('IDF_TARGET')!='esp32c3' or config.get('ESPTOOLPY_FLASHSIZE')!='8MB' or config.get('SPIRAM'):raise ValueError('wrong target, flash size or PSRAM setting')
    app=build/'passport_device.bin';elf=build/'passport_device.elf';table=build/'partition_table/partition-table.bin';boot=build/'bootloader/bootloader.bin'
    layout=partitions(table);factory=[p for p in layout if p['type']==0 and p['subtype']==0]
    if len(factory)!=1:raise ValueError('expected one factory application')
    factory=factory[0]
    if factory['offset']!=0x10000 or app.stat().st_size>factory['size']:raise ValueError('application does not fit the approved slot')
    data=app.read_bytes()
    if data[0]!=0xe9 or struct.unpack_from('<I',data,32)[0]!=0xabcd5432:raise ValueError('invalid ESP application descriptor')
    version=data[48:80].split(b'\0',1)[0].decode('ascii')
    project=data[80:112].split(b'\0',1)[0].decode('ascii')
    if project!='passport_device' or version!='0.5.21-aihot.1':raise ValueError('unexpected firmware version')
    embedded=data[176:208].hex()
    if embedded!=digest(elf):raise ValueError('application ELF identity does not match the build ELF')
    folder=ROOT/'releases'/f'Kai_ai-passport-suite-{version}-{digest(app)[:12]}'
    folder.mkdir(parents=True,exist_ok=True)
    files={'passport_device.bin':app,'bootloader.bin':boot,'partition-table.bin':table,'merged_flash.bin':build/'merged_flash.bin'}
    merged=files['merged_flash.bin'].read_bytes()
    for offset,segment in [(0,boot),(0x8000,table),(factory['offset'],app)]:
        image=segment.read_bytes()
        if merged[offset:offset+len(image)]!=image:raise ValueError(f'merged image does not contain matching {segment.name}')
    model=build/'srmodels.bin'
    if model.is_file():files['srmodels.bin']=model
    for name,source in files.items():shutil.copy2(source,folder/name)
    # The update plan contains only the application. The installer offers an erase choice; keep it unchecked.
    manifest={'name':'Kai AI Passport · AIHOT','version':version,'new_install_prompt_erase':True,'builds':[{'chipFamily':'ESP32-C3','parts':[{'path':'passport_device.bin','offset':factory['offset']}]}]}
    (folder/'update-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    segments=[{'path':'bootloader.bin','offset':0},{'path':'partition-table.bin','offset':0x8000},{'path':'passport_device.bin','offset':factory['offset']}]
    if model.is_file():segments.append({'path':'srmodels.bin','offset':0x670000})
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    metadata={'project':project,'version':version,'target':'esp32c3','flash_bytes':0x800000,'source_commit':revision,'source_dirty':dirty,
              'application_offset':factory['offset'],'application_elf_sha256':embedded,'partitions':layout,'update_parts':manifest['builds'][0]['parts'],'first_install_parts':segments,
              'files':{name:{'bytes':(folder/name).stat().st_size,'sha256':digest(folder/name)} for name in files},'device_tests':'NOT RUN',
              'data_policy':'Application-only update preserves existing data only when the on-device partition table matches. No erase-all is authorized. A merged image written at 0x0 can overwrite legacy NVS gaps.'}
    (folder/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (folder/'SHA256SUMS').write_text(''.join(f'{digest(folder/name)}  {name}\n' for name in files))
    for source in ['flash-guide.md','flash-guide.zh_CN.md']:shutil.copy2(ROOT/'docs'/source,folder/source)
    shutil.copy2(ROOT/'tools/browser-update.html',folder/'index.html')
    shutil.copy2(ROOT/'LICENSE',folder/'LICENSE')
    debug=ROOT/'build/firmware'/digest(app);debug.mkdir(parents=True,exist_ok=True)
    for name in ['passport_device.elf','passport_device.map','flasher_args.json','flash_args']:
        if (build/name).is_file():shutil.copy2(build/name,debug/name)
    shutil.copy2(folder/'manifest.json',debug/'manifest.json')
    archive=folder.parent/(folder.name+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as package:
        for path in sorted(folder.iterdir()):package.write(path,path.name)
    print(json.dumps({'folder':str(folder),'archive':str(archive),'app_sha256':digest(app),'elf_sha256':embedded,'debug':str(debug),'application_bytes':app.stat().st_size},indent=2))

if __name__=='__main__':main()
