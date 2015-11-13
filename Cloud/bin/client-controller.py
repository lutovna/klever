#!/usr/bin/env python3
import Cloud.utils as utils
import Cloud.controller as controller


if __name__ == "__main__":
    # Parse configuration
    conf = utils.common_initialization("Client controller")

    # Check config
    if "client-controller" not in conf:
        raise KeyError("Provide configuration property 'client-controller' as a JSON-object")
    if "node configuration" not in conf:
        raise KeyError("Provide configuration property 'node configuration' as a JSON-object")

    # Setup consul
    consul_work_dir, consul_config_file = controller.setup_consul(conf)

    # Run consul
    controller.run_consul(conf, consul_work_dir, consul_config_file)

__author__ = 'Ilja Zakharov <ilja.zakharov@ispras.ru>'
