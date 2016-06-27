import json, collections, subprocess, asyncio
from autobahn.asyncio.wamp import ApplicationSessionFactory

import logging

class Subscriber():
    """Subscribes to messages from WAMP Router on 'com.opentrons.browser_to_robot' and dispatches commands according to the :obj:`dispatcher` dictionary.

    
    The Subscriber class is intended to be intantiated into a subscriber object
    to dispatch commands from the GUI and ProtocolRunner to the appropriate object(s)
    for robot actions.

    The subscriber object holds references to all the relevant objects such
    as the head, queue objects etc.

    
    :dispatcher:
    * 'home' : lambda self, data: self.home(data),
    * 'stop' : lambda self, data: self.head.theQueue.kill(data),
    * 'reset' : lambda self: self.reset(),
    * 'move' : lambda self, data: self.head.move(data),
    * 'step' : lambda self, data: self.head.step(data),
    * 'calibratePipette' : lambda self, data: self.calibrate_pipette(data),
    * 'calibrateContainer' : lambda self, data: self.calibrate_container(data),
    * 'getCalibrations' : lambda self: self.get_calibrations(),
    * 'saveVolume' : lambda self, data: self.head.save_volume(data),
    * 'movePipette' : lambda self, data: self.move_pipette(data),
    * 'movePlunger' : lambda self, data: self.move_plunger(data),
    * 'speed' : lambda self, data: self.speed(data),
    * 'createDeck' : lambda self, data: self.create_deck(data),
    * 'instructions' : lambda self, data: self.instructions(data),
    * 'infinity' : lambda self, data: self.infinity(data),
    * 'pauseJob' : lambda self: self.head.theQueue.pause_job(),
    * 'resumeJob' : lambda self: self.head.theQueue.resume_job(),
    * 'eraseJob' : lambda self: self.runner.insQueue.erase_job(),
    * 'raw' : lambda self, data: self.head.raw(data),
    * 'update' : lambda self, data: self.loop.create_task(self.update(data)),
    * 'wifimode' : lambda self, data: self.wifi_mode(data),
    * 'wifiscan' : lambda self, data: self.wifi_scan(data),
    * 'hostname' : lambda self, data: self.change_hostname(data),
    * 'poweroff' : lambda self: self.poweroff(),
    * 'reboot' : lambda self: self.reboot(),
    * 'shareinet': lambda self: self.loop.create_task(self.share_inet()),
    * 'restart' : lambda self: self.restart()

    :todo:
    - clean up inclusion of head and runner objects -> referenced by dispatch
    - move publishing into respective objects and have those objects use :class:`publisher` a la :meth:`get_calibrations` (:meth:`create_deck`, :meth:`wifi_scan`)
    


    """
    
#Special Methods
    def __init__(self, session,loop):
        """Initialize Subscriber object
        """
        logging.info('subscriber.__init__ called')
        self.head = None
        self.deck = None
        self.runner = None
        self.caller = session
        self.loop = loop
        
    def __str__(self):
        return "Subscriber"


    def home(self, data):
        """Intermediate step to start a homing sequence
        """
        logging.debug('subscriber.home called')
        self.runner.insQueue.infinity_data = None
        self.runner.insQueue.erase_job()
        self.head.home(data)


    def reset(self):
        """Intermediate step to reset Smoothieboard
        """
        logging.debug('subscriber.reset called')
        self.runner.insQueue.infinity_data = None
        self.head.theQueue.reset()


    def set_head(self, head):
        """Set reference to :class:`head` object
        """
        logging.debug('subscriber.set_head called')
        self.head = head


    def set_deck(self, deck):
        self.deck = deck


    def set_runner(self, runner):
        """Set reference to :class:`protocol_runner` object
        """
        logging.debug('subscriber.set_runner called')
        self.runner = runner


    def dispatch_message(self, message):
        """The first point of contact for incoming messages.
        """
        logging.debug('subscriber.dispatch_message called')
        logging.debug('\nmessage: ',message,'\n')
        try:
            dictum = collections.OrderedDict(json.loads(message.strip(), object_pairs_hook=collections.OrderedDict))
            logging.debug('\tdictum[type]: ',dictum['type'])
            if 'data' in dictum:
                logging.debug('\tdictum[data]:\n\n',json.dumps(dictum['data'],sort_keys=True,indent=4,separators=(',',': ')),'\n')
                self.dispatch(dictum['type'],dictum['data'])
            else:
                self.dispatch(dictum['type'],None)
        except:
            logging.error('*** error in subscriber.dispatch_message ***')
            raise


    def dispatch(self, type_, data):
        """Dispatch commands according to :obj:`dispatcher` dictionary
        """
        logging.debug('subscriber.dispatch called')
        logging.debug('\n\n\ttype_: ',type_,'\n\tdata:',data,'\n')
        if data is not None:
            self.dispatcher[type_](self,data)
        else:
            self.dispatcher[type_](self)

          
    def calibrate_pipette(self, data):
        """Tell the :head:`head` to calibrate a :class:`pipette`
        """
        logging.debug('subscriber.calibrate_pipette called')
        logging.debug('\nargs: ', data,'\n')
        if 'axis' in data and 'property' in data:
            axis = data['axis']
            property_ = data['property']
            self.head.calibrate_pipette(axis, property_)
        self.get_calibrations()


    def calibrate_container(self, data):
        """Tell the :class:`head` to calibrate a container
        """
        logging.debug('subscriber.calibrate_container called')
        logging.debug('\nargs: ', data,'\n')
        if 'axis' in data and 'name' in data:
            axis = data['axis']
            container_ = data['name']
            self.head.calibrate_container(axis, container_)
        self.get_calibrations()


    def container_depth_override(self, data):
        logging.debug('subscriber.container_depth_override called')
        container_name = data['name']
        new_depth = data['depth']
        self.deck.container_depth_override(container_name,new_depth)


    def get_calibrations(self):
        """Tell the :class:`head` to publish calibrations
        """
        logging.debug('subscriber.get_calibrations called')
        self.head.publish_calibrations()

    def get_containers(self):
        self.deck.publish_containers()

    def move_pipette(self, data):
        """Tell the :class:`head` to move a :class:`pipette` 
        """
        logging.debug('subscriber.move_pipette called')
        axis = data['axis']
        property_ = data['property']
        self.head.move_pipette(axis, property_)


    def move_plunger(self, data):
        """Tell the :class:`head` to move a :class:`pipette` to given location(s)
        """
        logging.debug('subscriber.move_plunger called')
        logging.debug('\ndata:\n\t',data,'\n')
        self.head.move_plunger(data['axis'], data['locations'])


    def speed(self, data):
        """Tell the :class:`head` to change speed
        """
        logging.debug('subscriber.speed called')
        logging.debug('\ndata:\n\t',data,'\n')
        axis = data['axis']
        value = data['value']
        if axis=='ab':
            self.head.set_speed('a', value)
            self.head.set_speed('b', value)
        else:
            self.head.set_speed(axis, value)


    def create_deck(self, data):
        """Intermediate step to have :class:`head` load deck data and return deck information back to Browser

        :todo:
        move publishing into respective objects and have those objects use :class:`publisher` a la :meth:`get_calibrations` (:meth:`create_deck`, :meth:`wifi_scan`)
        """
        logging.debug('subscriber.create_deck called')
        logging.debug('\targs: ', data,'\n')
        msg = {
            'type' : 'containerLocations',
            'data' : self.head.create_deck(data)
        }
        logging.debug('pre-call self.caller._myAppSession.publish() ',json.dumps(msg,sort_keys=True,indent=4,separators=(',',': ')),'\n')
        self.caller._myAppSession.publish('com.opentrons.robot_to_browser',json.dumps(msg,sort_keys=True,indent=4,separators=(',',': ')))


    def configure_head(self, data):
        logging.debug('subscriber.configure_head called')
        logging.debug('\targs: ', data,'\n')
        self.head.configure_head(data)


    def instructions(self, data):
        """Intermediate step to have :class:`prtocol_runner` and :class:`the_queue` start running a protocol
        """
        logging.debug('subscriber.instructions called')
        logging.debug('\targs: ', data,'\n')
        if data and len(data):
            self.runner.insQueue.start_job (data, True)

    def infinity(self, data):
        """Intermediate step to have :class:`protocol_runner` and :class:`the_queue` run a protocol to infinity and beyond
        """
        logging.debug('subscriber.infinity called')
        if data and len(data):
            self.runner.insQueue.start_infinity_job (data)


    #instantiate/activate the dispatcher/router dictionary
    #create Dispatcher dictionary object which is the equivalent of the
    #previous socketHandlers object in js code
    dispatcher = {'home' : lambda self, data: self.home(data),
              'stop' : lambda self, data: self.head.theQueue.kill(data),
              'reset' : lambda self: self.reset(),
              'move' : lambda self, data: self.head.move(data),
              'step' : lambda self, data: self.head.step(data),
              'calibratePipette' : lambda self, data: self.calibrate_pipette(data),  #needs xtra code
              'calibrateContainer' : lambda self, data: self.calibrate_container(data),
              'getCalibrations' : lambda self: self.get_calibrations(),
              'saveVolume' : lambda self, data: self.head.save_volume(data),
              'movePipette' : lambda self, data: self.move_pipette(data),#needs xtra code
              'movePlunger' : lambda self, data: self.move_plunger(data),
              'speed' : lambda self, data: self.speed(data),          #needs xtra code
              'getContainers' : lambda self: self.get_containers(),
              'createDeck' : lambda self, data: self.create_deck(data),#needs xtra code
              'configureHead' : lambda self, data: self.configure_head(data),
              'relativeCoords' : lambda self: self.head.relative_coords(),
              'instructions' : lambda self, data: self.instructions(data),#needs xtra code
              'infinity' : lambda self, data: self.infinity(data),
              'pauseJob' : lambda self: self.head.theQueue.pause_job(),
              'resumeJob' : lambda self: self.head.theQueue.resume_job(),
              'eraseJob' : lambda self: self.runner.insQueue.erase_job(),
              'raw' : lambda self, data: self.head.raw(data),
              'update' : lambda self, data: self.loop.create_task(self.update(data)),
              'wifimode' : lambda self, data: self.wifi_mode(data),
              'wifiscan' : lambda self, data: self.wifi_scan(data),
              'hostname' : lambda self, data: self.change_hostname(data),
              'poweroff' : lambda self: self.poweroff(),
              'reboot' : lambda self: self.reboot(),
              'shareinet': lambda self: self.loop.create_task(self.share_inet()),
              'restart' : lambda self: self.restart(),
              'containerDepthOverride': lambda self, data: self.container_depth_override(data)
              }
    