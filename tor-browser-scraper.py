import requests, re, os, hashlib,  tarfile
from bs4 import BeautifulSoup
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile

def getVersion(tor_browser_version):
    m = re.search('linux(.+?)-', tor_browser_version)
    if m:
        found = m.group(1)
        return found

def compute_md5(file_name):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

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
    # tor_version = tor_version and '4.0.0' in tor_browser_version
    if tor_version:
        print('Checking ' + tor_browser_version)
        # Grab versions
        reqs = requests.get(url + tor_browser_version)
        soup = BeautifulSoup(reqs.text, 'html.parser')
        versions = soup.find_all('a')
        browser_file = '_en-US.tar.xz'
        for v in versions:
            browser_found = browser_file in v.get('href')
            browser_found = browser_found and '.asc' not in v.get('href') and '-'
            if browser_found:
                print(tor_browser_version + v.get('href'))
                # Download and extract
                print(url + tor_browser_version + v.get('href'))
                r = urlopen(url + tor_browser_version + v.get('href'))
                output_dir = tor_browser_version + 'x' + getVersion(v.get('href'))
                print(output_dir)
                compressed_file = None
                file_name = None
                key = None
                compressed_file = tarfile.open(name=None, fileobj=BytesIO(r.read()))
                ignored_directory = 'tor-browser_en-US/Browser/TorBrowser/Tor/PluggableTransports'
                binary_directory = 'tor-browser_en-US/Browser/TorBrowser/Tor'
                for member in compressed_file.getmembers():
                    # skip if the TarInfo is not a file and in the Tor folder
                    if  member.path.startswith(binary_directory) and member.isreg() and not member.path.startswith(ignored_directory):
                        print('Found Tor Binaries')
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

# Write Stats
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