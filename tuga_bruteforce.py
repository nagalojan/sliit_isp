
# Coded By IT20077792

# import go here
################################################################################
import os  # Miscellaneous operating system interfaces
import queue  # A synchronized queue class
import re  # Regular expression operations
import sys  # System-specific parameters and functions
import threading  # Thread-based parallelism
import time  # Time access and conversions
import dns.resolver  # dnspython
import datetime
# Import internal functions
from tuga_utils.colors import G, Y, B, R, W
from tuga_utils.dns import is_intranet
from tuga_utils.terminal import getTerminalSize
################################################################################
class TugaBruteForce:
    def __init__(self, options):
    # Namespace(domain='example.com', output=None, i=False, file='first_names.txt', savemap=False,
    #           bruteforce=True, threads=200, enum=None, full_scan=True)

        self.target = options.domain      # Target
        self.options = options            # All options...
        self.ignore_intranet = options.i  # need more options... not complete (Ignore domains pointed to private IPs)
        self.wordlist_subdomains = ""        # Wordlist

        # set threads and count system to 0
        self.thread_count = self.scan_count = self.found_count = 0
        self.lock = threading.Lock()

        # Resize Terminal
        self.console_width = getTerminalSize()[0] - 2  # thanks guys

        self.msg_queue = queue.Queue()
        self.STOP_SCAN = False

        # start the thread _print_msg by calling the start(). Terminal (self.console_width)
        threading.Thread(target=self._print_msg).start()

        # load DNS servers from a list (dns_servers.txt)
        self._load_dns_servers()

        # # Send 200 task requests to the worker. options.threads = 200 (default)
        self.resolvers = [dns.resolver.Resolver(configure=False) for number in range(options.threads)]
        for number in self.resolvers:
            number.lifetime = number.timeout = 6.0

        # Load second list name... (next_names.txt or next_names_full.txt)
        self._load_second_sub_names()
        self.queue = queue.Queue()  # Create a queue to communicate with the worker threads

        # # Turn-on the worker thread. Load the first list name... (thread)
        t = threading.Thread(target=self._load_first_sub_names)
        t.start() # start the thread for the first list name...

        while not self.queue.qsize() > 0 and t.is_alive():
            time.sleep(0.1)

        # create a target folder and save results in to a file txt
        #if options.output:
        #    outfile = options.output
        date = str(datetime.datetime.now().date())
        pwd = os.getcwd()
        #############
        # saving subdomains results to output file
        folder = os.path.join(pwd, "results/" + self.target + "/" + date)
        try:
            os.makedirs(folder)
        except:
            pass
        outfile = 'results/' + self.target + "/" + date  + "/" + '_subdom_bruteforce.txt' if not options.full_scan else 'results/' + self.target + "/" + date + "/" + '_tuga_bruteforce_full.txt'
        self.outfile = open(outfile, 'w')
################################################################################
        # save ip, dns.
        self.ip_dict = {}
        self.last_scanned = time.time()
        self.ex_resolver = dns.resolver.Resolver(configure=False)
        self.start_time = None
################################################################################
    def _load_dns_servers(self):
        # dns_servers.txt
        try:
            print(G + '[+] Initializing, validate DNS servers ...')
            self.dns_servers = []
            with open('wordlist/dns_servers.txt') as f:
                for line in f:
                    server = line.strip()
                    if not server:
                        continue
                    while True:
                        if threading.activeCount() < 50: # default 50
                            t = threading.Thread(target=self._test_dns_servers, args=(server,)) # Testing DNS servers...
                            t.start() # start the thread
                            break
                        else:
                            time.sleep(0.1)

            while threading.activeCount() > 2:
                time.sleep(0.1)
            self.dns_count = len(self.dns_servers)  # count the number of DNS servers
            #sys.stdout.write('\n')
            print('[+] Found %s available DNS Servers' % self.dns_count)
            if self.dns_count == 0:
                print('[ERROR] Oops! No DNS Servers available.')
                self.STOP_SCAN = True
                sys.exit(-1)
        except KeyboardInterrupt:
            print("\nTugaRecon interrupted by user\n")
            quit()
################################################################################
    def _test_dns_servers(self, server):
        # dns_servers.txt
        resolver = dns.resolver.Resolver(configure=False)
        resolver.lifetime = resolver.timeout = 10.0
        try:
            resolver.nameservers = [server]
            answers = resolver.query('s-coco-ns01.co-co.nl')  # test lookup a existed domain
            if answers[0].address != '188.122.89.156':
                raise Exception('incorrect DNS response')
            try:
                resolver.query('test.bad.dns.skynet0x01.pt')  # Non-existed domain test
                with open('wordlist/bad_dns_servers.txt', 'a') as f:
                    f.write(server + '\n')
                    # Put an item into the queue.
                    # If the queue is full, wait until a free slot is available before adding the item.
                self.msg_queue.put('[+] Bad DNS Server found %s' % server)
            except:
                self.dns_servers.append(server) # Adding elements to self.dns_servers
            self.msg_queue.put('[+] Check DNS Server %s < OK >   Found %s' % (server.ljust(16), len(self.dns_servers)))
        except:
            self.msg_queue.put('[+] DNS Server %s <Fail>   Found %s' % (server.ljust(16), len(self.dns_servers)))
################################################################################
    def _load_first_sub_names(self):

        # Verify the first wordlist
        if self.options.full_scan and self.options.file == 'first_names.txt':
            _file = 'wordlist/first_names_full.txt'
            self.msg_queue.put('[+] Load the first list...   ' + _file)
        else:
            if os.path.exists(self.options.file):
                _file = self.options.file
                self.msg_queue.put('[+] Load the first list...   ' + _file)
            elif os.path.exists('wordlist/%s' % self.options.file):
                _file = 'wordlist/%s' % self.options.file
                self.msg_queue.put('[+] Load the first list...   ' + _file)
            else:
                self.msg_queue.put('[ERROR] [WORDLIST] Oops! File not exists: %s' % self.options.file)
                return

        # Wildcard --------------------------------------------------
        # Put an item into the queue.
        # If the queue is full, wait until a free slot is available before adding the item.
        self.msg_queue.put('[+] Prepare the wildcard...')
        self.msg_queue.put('[+] DONE...')
        self.msg_queue.put('[+] Search for subdomains...\n' + W)

        normal_lines = []
        wildcard_lines = []
        wildcard_list = []
        regex_list = []
        lines = set()

        # Open the first list names
        with open(_file) as f:
            for line in f:
                sub = line.strip()
                #print(sub)
                if not sub or sub in lines:
                    #print(sub)
                    continue
                lines.add(sub)
                if sub.find('{alphnum}') >= 0 or sub.find('{alpha}') >= 0 or sub.find('{num}') >= 0:
                    wildcard_lines.append(sub) # Adding elements to wildcard_lines
                    sub = sub.replace('{alphnum}', '[a-z0-9]')
                    sub = sub.replace('{alpha}', '[a-z]')
                    sub = sub.replace('{num}', '[0-9]')
                    if sub not in wildcard_list:
                        wildcard_list.append(sub) # Adding elements to wildcard_list
                        regex_list.append('^' + sub + '$') # Adding elements to regex_list
                else:
                    normal_lines.append(sub) # Adding elements to normal_lines
        pattern = '|'.join(regex_list)
        if pattern:
            _regex = re.compile(pattern)
            if _regex:
                for line in normal_lines:
                    if _regex.search(line):
                        normal_lines.remove(line)
        lst_subs = []
        GROUP_SIZE = 1 if not self.options.full_scan else 1  # disable scan by groups

        for item in normal_lines:
            lst_subs.append(item)
            if len(lst_subs) >= GROUP_SIZE:
                self.queue.put(lst_subs)
                lst_subs = []

        sub_queue = queue.LifoQueue()
        for line in wildcard_lines:
            sub_queue.put(line)
            while sub_queue.qsize() > 0:
                item = sub_queue.get() # Remove and return an item from the queue. If queue is empty, wait until an item is available.
                if item.find('{alphnum}') >= 0:
                    for _letter in 'abcdefghijklmnopqrstuvwxyz0123456789':
                        sub_queue.put(item.replace('{alphnum}', _letter, 1))
                elif item.find('{alpha}') >= 0:
                    for _letter in 'abcdefghijklmnopqrstuvwxyz':
                        sub_queue.put(item.replace('{alpha}', _letter, 1))
                elif item.find('{num}') >= 0:
                    for _letter in '0123456789':
                        sub_queue.put(item.replace('{num}', _letter, 1))
                else:
                    lst_subs.append(item)
                    if len(lst_subs) >= GROUP_SIZE:
                        while self.queue.qsize() > 10000:
                            time.sleep(0.1)
                        self.queue.put(lst_subs)
                        lst_subs = []
        if lst_subs:
            self.queue.put(lst_subs)
################################################################################
    def _load_second_sub_names(self):

        # Verify the next wordlist
        _file = 'wordlist/next_names.txt' if not self.options.full_scan else 'wordlist/next_names_full.txt'

        self.msg_queue.put('\n[+] Load the second list...  ' + _file)
        next_subs = []

        # Wildcard
        with open(_file) as f:
            for line in f:
                sub = line.strip()
                if sub and sub not in next_subs:
                    tmp_set = {sub}
                    while len(tmp_set) > 0:
                        item = tmp_set.pop() # Removing elements from the tmp_set
                        if item.find('{alphnum}') >= 0:
                            for _letter in 'abcdefghijklmnopqrstuvwxyz0123456789':
                                tmp_set.add(item.replace('{alphnum}', _letter, 1))
                        elif item.find('{alpha}') >= 0:
                            for _letter in 'abcdefghijklmnopqrstuvwxyz':
                                tmp_set.add(item.replace('{alpha}', _letter, 1))
                        elif item.find('{num}') >= 0:
                            for _letter in '0123456789':
                                tmp_set.add(item.replace('{num}', _letter, 1))
                        elif item not in next_subs:
                            next_subs.append(item)
        self.next_subs = next_subs
        #print(self.next_subs) #just for test
################################################################################
    def _update_scan_count(self):
        self.last_scanned = time.time()
        self.scan_count += 1
################################################################################
    def _update_found_count(self):
        # no need to use a lock
        self.found_count += 1
################################################################################
    def _print_msg(self):
        while not self.STOP_SCAN:
            try:
                # Queue.get( block = True , timeout = None )
                _msg = self.msg_queue.get(timeout=0.1) # _msg (subdomains), timeout=0.1
            except:
                continue
            if _msg == 'status':
                msg = ' %s  | Found %s subdomains | %s groups left | %s scanned in %.1f seconds| %s threads' % (
                     self.wordlist_subdomains, self.found_count, self.queue.qsize(), self.scan_count, time.time() - self.start_time,
                    self.thread_count)
                sys.stdout.write('\r' + ' ' * (self.console_width - len(msg)) + msg) # print Found 6 subdomains | 0 groups left | 26274 scanned in 49.0 seconds| 199 threads
            elif _msg.startswith('[+] Check DNS Server'):
                sys.stdout.write('\r' + _msg + ' ' * (self.console_width - len(_msg))) # print Check DNS
            else:
                sys.stdout.write('\r' + _msg + ' ' * (self.console_width - len(_msg)) + '\n')  # _msg print subdomains in console
            sys.stdout.flush()
################################################################################
    def _scan(self):
        thread_id = int(threading.currentThread().getName())
        self.resolvers[thread_id].nameservers = [self.dns_servers[thread_id % self.dns_count]]
        _lst_subs = []
        self.lock.acquire()
        self.thread_count += 1
        self.lock.release()

        while not self.STOP_SCAN:
            if not _lst_subs:
                try:
                    _lst_subs = self.queue.get(timeout=0.1) # Remove and return an item from the queue. If queue is empty, wait until an item is available.
                except:
                    if time.time() - self.last_scanned > 2.0: # default 2.0
                        break
                    else:
                        continue
            # print(_lst_subs) result words list ['oscommerce']
            sub = _lst_subs.pop() # Removing elements from the _lst_subs print(_lst_subs) result empty [] pass to sub
            #print(sub)
            _sub = sub.split('.')[-1]
            #print(_sub)
            _sub_timeout_count = 0
            while not self.STOP_SCAN:
                try:
                    cur_sub_domain = sub + '.' + self.target
                    self.wordlist_subdomains = cur_sub_domain
                    self._update_scan_count()
                    self.msg_queue.put('status')
                    try:
                        answers = self.resolvers[thread_id].query(cur_sub_domain)   # Testing subdomains...
                        #for server in answers:
                        #    print(server.to_text())
                    except dns.resolver.NoAnswer as e:
                        answers = self.ex_resolver.query(cur_sub_domain)

                    is_wildcard_record = False

                    if answers:
                        ips = ', '.join(sorted([answer.address for answer in answers]))
                        if ips in ['192.168.1.1', '127.0.0.1', '0.0.0.0']:
                            break
                        if (_sub, ips) not in self.ip_dict:
                            self.ip_dict[(_sub, ips)] = 1
                        else:
                            self.ip_dict[(_sub, ips)] += 1
                        if ips not in self.ip_dict:
                            self.ip_dict[ips] = 1
                        else:
                            self.ip_dict[ips] += 1
                        if self.ip_dict[(_sub, ips)] > 3 or self.ip_dict[ips] > 6:
                            is_wildcard_record = True
                        if is_wildcard_record:
                            break
                        if (not self.ignore_intranet) or (not is_intranet(answers[0].address)):
                            self._update_found_count()
                            msg = cur_sub_domain.ljust(50) + ips  # default [30, 50], msg = <subs>.<target> and info.
                            self.msg_queue.put(msg)
                            self.msg_queue.put('status')
                            self.outfile.write(cur_sub_domain.ljust(50) + '\t' + ips + '\n') #Write to a file
                            self.outfile.flush()
                            try:
                                self.resolvers[thread_id].query('lordneostark.' + cur_sub_domain)
                            except dns.resolver.NXDOMAIN as e:
                                _lst = []
                                if_put_one = (self.queue.qsize() < self.dns_count * 5)
                                for i in self.next_subs:
                                    _lst.append(i + '.' + sub)
                                    if if_put_one:
                                        self.queue.put(_lst)
                                        _lst = []
                                    elif len(_lst) >= 10:
                                        self.queue.put(_lst)
                                        _lst = []
                                if _lst:
                                    self.queue.put(_lst)
                            except:
                                pass
                        break
                except (dns.resolver.NXDOMAIN, dns.name.EmptyLabel) as e:
                    break
                except (dns.resolver.NoNameservers, dns.resolver.NoAnswer, dns.exception.Timeout) as e:
                    _sub_timeout_count += 1
                    if _sub_timeout_count >= 6:  # give up default 6
                    # TEST
                        #msg = cur_sub_domain.ljust(50)
                        #self.msg_queue.put(R + msg + 'DNS timeout...!?' + W)
                        #self.outfile.write(cur_sub_domain.ljust(50) + '\t' + 'DNS timeout!? \n')
                        #self.outfile.flush()
                    # TEST END
                        break
                except Exception as e:
                    with open('errors.log', 'a') as errFile:
                        errFile.write('%s [%s] %s %s\n' % (threading.current_thread, type(e), cur_sub_domain, e))
                    break
        self.lock.acquire()
        self.thread_count -= 1
        self.lock.release()
        self.msg_queue.put('status')
################################################################################
    def run(self):
        self.start_time = time.time()
        # Send 200 task requests to the workers.
        for i in range(self.options.threads):
            try:
                # Turn-on the worker thread.
                t = threading.Thread(target=self._scan, name=str(i))
                t.setDaemon(True)
                t.start() # start the thread for the def _scan()
            except:
                pass
        while self.thread_count > 0:
            try:
                time.sleep(0.1)  # time sleep 1, try to change to 0.1 or 0
            except KeyboardInterrupt as e:
                msg = (R + '[WARNING] User aborted, wait all slave threads to exit...' + W)
                sys.stdout.write('\r' + msg + ' ' * (self.console_width - len(msg)) + '\n\r')
                sys.stdout.flush()
                self.STOP_SCAN = True
        self.STOP_SCAN = True
################################################################################
