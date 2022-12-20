import requests, re, os, hashlib,  tarfile
from bs4 import BeautifulSoup
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile

def getVersion(tor_browser_version):
    m = re.search('tor-linu(.+?)-debug', tor_browser_version)
    if m:
        found = m.group(1)
        return found

def compute_md5(file_name):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def removeEmptyFolders(path, removeRoot=True):
  if not os.path.isdir(path):
    return
  # remove empty subfolders
  files = os.listdir(path)
  if len(files):
    for f in files:
      fullpath = os.path.join(path, f)
      if os.path.isdir(fullpath):
        removeEmptyFolders(fullpath)

  # if folder empty, delete it
  files = os.listdir(path)
  if len(files) == 0 and removeRoot:
    os.rmdir(path)



url = 'https://archive.torproject.org/tor-package-archive/torbrowser/'
reqs = requests.get(url)
soup = BeautifulSoup(reqs.text, 'html.parser')

urls = soup.find_all('a')

# dictionary of key = md5, value = list of versions

version_tracker32 = {}
version_tracker64 = {}
for u in urls:
    tor_browser_version = u.get('href')

    # Filter top level torbrowser versions
    tor_version = '.' in tor_browser_version and 'tor' not in tor_browser_version
    tor_version = tor_version and 'old' not in tor_browser_version 
    tor_version = tor_version and '.tgz' not in tor_browser_version
    tor_version = tor_version and '.asc' not in tor_browser_version 
    tor_version = tor_version and '.zip' not in tor_browser_version

    # Force version for testing
    tor_version = tor_version and '3.' in tor_browser_version

    if tor_version:
        print('Checking ' + tor_browser_version)
        # Grab versions
        reqs = requests.get(url + tor_browser_version)
        soup = BeautifulSoup(reqs.text, 'html.parser')
        versions = soup.find_all('a')
        debug_version32 = 'tor-linux32-debug'
        debug_version64 = 'tor-linux64-debug'
        for v in versions:
            debug_found = debug_version32 in v.get('href')
            debug_found = debug_found or debug_version64 in v.get('href') 
            debug_found = debug_found and '.asc' not in v.get('href')
            if debug_found:
                print(tor_browser_version + v.get('href'))
                # Download and extract
                r = urlopen(url + tor_browser_version + v.get('href'))
                output_dir = tor_browser_version + getVersion(v.get('href'))
                compressed_file = None
                file_name = None
                key = None
                if '.tar' in v.get('href'):
                    compressed_file = tarfile.open(name=None, fileobj=BytesIO(r.read()))
                    for member in compressed_file.getmembers():
                        # skip if the TarInfo is not files
                        if member.isreg():
                            member.name = os.path.basename(member.name) 
                            compressed_file.extract(member,output_dir)
                            file_name = output_dir + '/' + member.name
                            md5 = compute_md5(file_name)
                            key = member.name + ':' + md5
                            # if x32 or x64 architeture, add the version to the file name and hash version dictionary
                            if 'x32' in file_name:
                                if key in version_tracker32:
                                    version_tracker32[key].append(tor_browser_version[0:len(tor_browser_version)-1])
                                    # If key is already in tracker, then delete this file to avoid duplicates
                                    os.remove(file_name)
                                else:
                                    version_tracker32[key] = []
                                    version_tracker32[key].append(tor_browser_version[0:len(tor_browser_version)-1])
                            if 'x64' in file_name:
                                if key in version_tracker64:
                                    version_tracker64[key].append(tor_browser_version[0:len(tor_browser_version)-1])
                                    # If key is already in tracker, then delete this file to avoid duplicates
                                    os.remove(file_name)
                                else:
                                    version_tracker64[key] = []
                                    version_tracker64[key].append(tor_browser_version[0:len(tor_browser_version)-1])    
                if '.zip' in v.get('href'):
                    compressed_file = ZipFile(BytesIO(r.read()))
                    for f in compressed_file.infolist():
                        if f.filename[-1] != '/':
                            f.filename = os.path.basename(f.filename)
                            compressed_file.extract(f, output_dir)
                            file_name = output_dir + '/' + f.filename
                            md5 = compute_md5(file_name)
                            key = f.filename + ':' + md5
                            # if x32 or x64 architeture, add the version to the file name and hash version dictionary
                            if 'x32' in file_name:
                                if key in version_tracker32:
                                    version_tracker32[key].append(tor_browser_version[0:len(tor_browser_version)-1])
                                    # If key is already in tracker, then delete this file to avoid duplicates
                                    os.remove(file_name)
                                else:
                                    version_tracker32[key] = []
                                    version_tracker32[key].append(tor_browser_version[0:len(tor_browser_version)-1])
                            if 'x64' in file_name:
                                if key in version_tracker64:
                                    version_tracker64[key].append(tor_browser_version[0:len(tor_browser_version)-1])
                                    # If key is already in tracker, then delete this file to avoid duplicates
                                    os.remove(file_name)
                                else:
                                    version_tracker64[key] = []
                                    version_tracker64[key].append(tor_browser_version[0:len(tor_browser_version)-1])

# Remove Empty Folder if any...
removeEmptyFolders(os.path.dirname(os.path.realpath(__file__)), True)


f = open("library_comparison.txt", "w")
f.write('Format\n')
f.write('filename:hash | version1, version1.2, etc...\n')
f.write('\n----------------x32-----------------\n')
for k,  v in version_tracker32.items():
    f.write(k + ' | ' + ' , '.join([str(elem) for elem in v]) + "\n")

f.write('\n----------------x64-----------------\n')
for k,  v in version_tracker64.items():
    f.write(k + ' | ' + ' , '.join([str(elem) for elem in v]) + "\n")
f.close()
