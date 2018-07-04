#!/usr/bin/env python

import sys
import argparse
from configobj import ConfigObj

from suds.client import Client
from suds.sax.element import Element


class Session:

    def __init__(self, globalconfigfile="global.conf", sessionconfigfile="session.conf"):
        self.globalconfigfile = globalconfigfile
        self.sessionconfigfile = sessionconfigfile
        self.globalconfig = {}
    
    def readConfig(self):
        globalconfig = ConfigObj(self.globalconfigfile)
    
        serversection = globalconfig['Server']
        baseURL = serversection['baseURL']
    
        usersection = globalconfig['User']
        username = usersection['username']
        password = usersection['password']

        webservice = usersection['webservice']
        webservicefile = usersection['webservicefile']
    
        spenvissection = globalconfig['Spenvis']
        ns = spenvissection['ns']
        mainurl = spenvissection['mainurl']

        self.globalconfig = {
            "baseURL":baseURL,"username":username,
            "password":password,"webservice":webservice,"webservicefile":webservicefile,
            "spenvissection":spenvissection,"ns":ns,"mainurl":mainurl,
        }


    def login(self):

        url = "/".join([self.globalconfig["baseURL"],
                        self.globalconfig["webservice"],self.globalconfig["webservicefile"]])
        clientlogin = Client(url)
        token = clientlogin.service.authenticate(username=self.globalconfig["username"],
                                             password=self.globalconfig["password"])

        ssnns = (self.globalconfig["ns"], self.globalconfig["mainurl"])
        ssn = Element('SecureToken', ns=ssnns).setText(token)

        return ssn

    def execute(self,ssn):

        sessionconfig = ConfigObj(self.sessionconfigfile)

        for s in sessionconfig.sections:

            section = sessionconfig[s]
            url = "/".join([self.globalconfig["baseURL"],section["webservice"],section["webservicefile"]])
            client = Client(url)
            client.set_options(soapheaders=ssn)

            for operation in section.sections:

                params = list(section[operation].values())
                paramlist = []

                inipos = client.__str__().find(operation)+len(operation)+1
                endpos = client.__str__()[inipos:-1].find(" ") + inipos
                objecttype = client.__str__()[inipos:endpos]
                p = client.factory.create(objecttype)

                for param in params:
                    setattr(p,param[0],param[1])
                    paramlist.append(p)

                op = getattr(client.service, operation)
                result = op(paramlist)

                print(result)


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Manage SPENVIS through console')

    parser.add_argument('--globalconfig', default='global.conf', help='Global configuration file')
    parser.add_argument('--sessionconfig', default='session.conf', help='Session configuration file')
    parser.add_argument('--test', default='no', help='Activate safe test mode (yes/no)')
    
    args = vars(parser.parse_args())

    globalconfig = ConfigObj(args['globalconfig'])

    s = Session(args['globalconfig'],args['sessionconfig'])
    s.readConfig()
    ssn = s.login()
    s.execute(ssn)

    sys.exit(0)
