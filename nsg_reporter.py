import vspk.v5_0 as vspk
import vspk.utils as utils
import requests
import urllib3
from pprint import pprint as pprint
import logging
import bambou
import time
import re
import xlsxwriter
import argparse


# Support classes

class NSGRecord:
    """This class used to represent NSG object and related information for the purpose to build usage report."""

    ___version___ = '1.0'

    __doc__ = """This class used to represent NSG object and related information for the purpose to build usage
                report."""
    _nunsgateway_attr_list = ['name', 'uuid', 'system_id', 'enterprise_id', 'serial_number', 'personality',
                              'operation_status', 'creation_date', 'last_updated_date', 'bootstrap_status',
                              'nsg_version']
    _extended_attr_list = {'enterprise_name': ''}

    nsg = None
    _state = 'UNDEF'
    _api = None

    def __init__(self, nsg_gw, api=None):
        self.nsg = nsg_gw
        self._state = 'INIT'
        if not api is None:
            self._api = api
            self._state = 'EINIT'

    def __getattr__(self, name) -> object:
        if self._state == 'INIT' or self._state == 'FETCHED':
            if name in self._nunsgateway_attr_list:
                print('i am here')
                if self._state == 'INIT':
                    nsg.fetch()
                    self._state = 'FETCHED'
                return eval('self.nsg.' + name)
        # With extended attributes
        elif self._state == 'EINIT' or self._state == 'EFETCHED':
            if name in self._nunsgateway_attr_list:

                if self._state == 'EINIT':
                    nsg.fetch()
                    self._state = 'EFETCHED'
                if re.findall('date', name):
                    st = eval('self.nsg.' + name)
                    return time.ctime(st)
                return eval('self.nsg.' + name)

            if name in [*self._extended_attr_list]:
                # Now extended attr to be populated
                if name == 'enterprise_name':
                    ents = self._api.enterprises.get()
                    for e in ents:
                        e.fetch()
                        if e.id == self.nsg.enterprise_id:
                            self._extended_attr_list['enterprise_name'] = e.name
                            return self._extended_attr_list['enterprise_name']
                    # If it's not found within enterprise, then set it to 'csp'
                    self._extended_attr_list['enterprise_name'] = 'csp'
                    return self._extended_attr_list['enterprise_name']

        # TODO: Add egress rate here
        raise AttributeError("{} object has no attribute {}!".format(self, name))

    def __str__(self) -> str:
        """
        __str__ method implementation
        :return:
        """
        str_res = []
        for attr in self._nunsgateway_attr_list:
            str_res.append("{0!s:<20} : {1!s:>40}".format(attr, eval('self.' + attr)))
        for attr in self._extended_attr_list:
            str_res.append("{0!s:<20} : {1!s:>40}".format(attr, eval('self.' + attr)))
        return '\n'.join(str_res)

    def csv(self) -> str:
        """
        The function returns csv requence
        :return: str
        """
        str_res = []
        for attr in self._nunsgateway_attr_list:
            str_res.append("{0!s:<}".format(eval('self.' + attr)))
        for attr in self._extended_attr_list:
            str_res.append("{0!s:<}".format(eval('self.' + attr)))
        return ','.join(str_res)

    @staticmethod
    def imp_nsg_attrs() -> list:
        """
        Returns list of NSG attrs implemented by the class
        :return: list
        """
        return NSGRecord._nunsgateway_attr_list + [*NSGRecord._extended_attr_list]

    def attr_list(self) -> list:
        """
        The function return the list of ordered attribute values in accordance with NSGRecord.imp_nsg_attrs()
        :return: list
        """
        attr_list = []
        for attr in self._nunsgateway_attr_list:
            attr_list.append(eval('self.' + attr))
        for attr in self._extended_attr_list:
            attr_list.append(eval('self.' + attr))
        return attr_list


# Support functions


def fetch_child_objects(obj: object) -> list:
    """ The function is fetching all child objects names. """

    c_ents = obj.children_rest_names
    for c in c_ents:
        # Print all child entries for provided object
        pprint(str(type(obj)) + ' child:  ' + str(c))


def nu_get_supported_api_versions(base_url: str) -> list:
    """ The function requests all possible api versions and selects CURRENT one. """

    http_session = requests.session()
    http_resp = http_session.get(url=base_url, verify=False)

    if http_resp.ok:
        json_obj = http_resp.json()
    ver_supp = []
    # Go throughout list of dicts and extract CURRENT versions
    for item in json_obj['versions']:
        if item['status'] == 'CURRENT':
            ver_supp.append(item['version'].upper())
    # Let's return most recent version as [0]
    ver_supp.sort(reverse=True)
    return ver_supp


def nu_build_api_url(host_base: str) -> str:
    return host_base + '/nuage/api/' + nu_get_supported_api_versions(host_base + '/nuage')[0]


# Main function

if __name__ == '__main__':

    # Setting up main logger and logger for NuAPI
    main_logger = logging.getLogger('__name__')
    fl_hdl = logging.FileHandler(__name__ + '.log', mode='w')
    fl_hdl.setLevel(logging.DEBUG)
    fl_hdl.setFormatter(logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s: %(message)s'))
    main_logger.addHandler(fl_hdl)
    main_logger.setLevel(logging.DEBUG)
    utils.set_log_level(logging.DEBUG, logging.FileHandler('nu_api.log', mode='w'))
    main_logger.debug("***  START  ***")

    # Parsing arguments...
    main_logger.debug("Parsing arguments...")
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', help='VSD IP address or FQDN', action='append', required=True)
    parser.add_argument('-l', help='user login [csproot rights]', action='append', default=['csproot'])
    parser.add_argument('-p', help='csproot password', action='append', default=['csproot'])
    parser.add_argument('--csv', help='print report in stdout in CSV format', action='store_true')
    parser.add_argument('--xlsx', help='create report in XLSX format, file name should be provided', action='append')
    parser.add_argument('--show', help='show pretty text report in stdout', action='store_true')
    args = parser.parse_args()

    # Disable exceptions related to incorrect SSL certificates
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    api_base = nu_build_api_url('https://vsd1a.nuage.cf:8443')
    # Prints current API URL
    main_logger.debug('Current API URL: ' + api_base)

    api_session = vspk.NUVSDSession(username=args.l[0], password=args.p[0], enterprise='csp',
                                    api_url='https://' + args.v[0] + ':8443')

    # Actively connecting to the VSD API
    main_logger.debug("Actively connecting to the VSD API")
    try:
        api_session.start()
    except bambou.exceptions.BambouHTTPError as err:
        response = err.connection.response
        if response.status_code == 409:
            # The entity probably already exists, so we just ignore this error:
            pass
        else:
            main_logger.error("Failed to start session! Exiting...")
            # re-raise the exception
            raise

    # Getting root
    api_user = api_session.user
    main_logger.debug("Get api_user.")
    # List of NSGRecord objects
    nsg_records = []

    # Populate data for NSG records
    main_logger.debug("Starts populating NSG records")
    csproot_ents = api_user.enterprises.get()
    for ent in csproot_ents:
        ent.fetch()
        ent_nsgs = ent.ns_gateways.get()

        for nsg in ent_nsgs:
            nsgr = NSGRecord(nsg, api_user)
            nsg_records.append(nsgr)

    if args.show:
        # Print petty text
        main_logger.debug("Printing pretty attribute text representation.")
        for nsgr in nsg_records:
            print(nsgr)

    if args.csv:
        # Print nsg attr in csv format
        main_logger.debug("CSV output option was selected.")
        for nsgr in nsg_records:
                print(nsgr.csv())

    if args.xlsx:
        # Creating report in XLSX format
        main_logger.debug("XLSX output option was selected.")
        xlsx_filename = args.xlsx[0]
        workbook = xlsxwriter.Workbook(xlsx_filename)
        ws_time = re.sub(':', '.', time.ctime())
        worksheet = workbook.add_worksheet(name='NSG ' + ws_time)
        """
        Creating headers and fill NSG names
        NSG name | <Attr1> | <Attr2>
        <nsg 01> |         |
        <nsg 02> |         |
        """
        header_cell_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#0066cc'})
        header_cell_format.set_center_across()
        header_cell_format.set_border()
        data_cell_format = workbook.add_format()
        data_cell_format.set_border()
        worksheet.write_row('A1', NSGRecord.imp_nsg_attrs(), header_cell_format)
        row = 1
        for nsgr in nsg_records:
            worksheet.write_row(row, 0, nsgr.attr_list(), data_cell_format)
            row += 1
        workbook.close()

    exit(0)
