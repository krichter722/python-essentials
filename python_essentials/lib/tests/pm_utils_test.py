#!/usr/bin/python
# -*- coding: utf-8 -*- 

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Dieses Programm ist Freie Software: Sie können es unter den Bedingungen
#    der GNU General Public License, wie von der Free Software Foundation,
#    Version 3 der Lizenz oder (nach Ihrer Wahl) jeder neueren
#    veröffentlichten Version, weiterverbreiten und/oder modifizieren.
#
#    Dieses Programm wird in der Hoffnung, dass es nützlich sein wird, aber
#    OHNE JEDE GEWÄHRLEISTUNG, bereitgestellt; sogar ohne die implizite
#    Gewährleistung der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
#    Siehe die GNU General Public License für weitere Details.
#
#    Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
#    Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

import random
import unittest
import pm_utils
import tempfile
import os

class PMUtilsTest(unittest.TestCase):

    def test_check_apt_source_line_added(self):
        temp_dir = tempfile.mkdtemp()
        uri = "http://foo.bar/foobar"
        component = "main"
        distribution = "dist"
        the_type = "deb"
        sources_dir_path = os.path.join(temp_dir, "etc/apt/sources.list.d")
        sources_file_path = os.path.join(temp_dir, "etc/apt/sources.list")
        # test ValueError raised when sources_dir_path doesn't exist
        self.assertRaises(ValueError, pm_utils.check_apt_source_line_added, uri, component, distribution, the_type, "/nonexistent.d/")
        os.makedirs(sources_dir_path)
        open(sources_file_path, "w").close()
        # test not found is nothing specified
        found = pm_utils.check_apt_source_line_added(uri, component, distribution, the_type, augeas_root=temp_dir)
        self.assertEqual(found, False)
        # test returning false when commented is present in sources directory
        sources_dir_file_path = tempfile.mkstemp(dir=sources_dir_path)[1]
        sources_dir_file = open(sources_dir_file_path, "w")
        sources_dir_file.write("#%s %s %s %s\n" % (the_type, uri, distribution, component))
        sources_dir_file.flush()
        sources_dir_file.close()
        found = pm_utils.check_apt_source_line_added(uri, component, distribution, the_type, augeas_root=temp_dir)
        self.assertEqual(found, False)
        # test returning false when commented entry is present in both sources directory and sources file
        sources_file = open(sources_file_path, "w")
        sources_file.write("#%s %s %s %s\n" % (the_type, uri, distribution, component))
        sources_file.flush()
        sources_file.close()
        found = pm_utils.check_apt_source_line_added(uri, component, distribution, the_type, augeas_root=temp_dir)
        self.assertEqual(found, False)
        # test returning true when entry in sources directory present besides commented entry in sources file and commented entry in other file in sources directory
        sources_dir_file_path1 = tempfile.mkstemp(dir=sources_dir_path)[1]
        sources_dir_file = open(sources_dir_file_path1, "w")
        sources_dir_file.write("%s %s %s %s\n" % (the_type, uri, distribution, component))
        sources_dir_file.flush()
        sources_dir_file.close()
        found = pm_utils.check_apt_source_line_added(uri, component, distribution, the_type, augeas_root=temp_dir)
        self.assertEqual(found, True)

if __name__ == '__main__':
    unittest.main()

