import time

import requests
import unittest
import sys
import argparse
import os
import csv

GAME_NAME = "dancer"
LEVEL = "1"

class APITestCase(unittest.TestCase):

    def setUp(self):
        print(f"running tests with parameters from {current_path}:")
        # Set up any necessary configurations or variables
        self.user_name = args.user_name
        self.password = args.password
        self.token = None
        self.base_url = "http://localhost:3001/api"
        self.game_name = GAME_NAME
        self.level = LEVEL

        with open(current_path, 'r') as file:
            # Create a CSV reader object
            reader = csv.reader(file)
            self.add_commands_data = next(reader)
            self.swap_commands_data = next(reader)
            self.delete_commands_data = next(reader)

    def login(self):
        url = f"{self.base_url}/users/login"
        data = {"name": self.user_name, "password": self.password}
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()['token'])
        self.token = response.json()['token']

    def get_level_data(self):
        url = f"{self.base_url}/{self.game_name}/levels/getOne/{self.level}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def add_commands(self):
        url = f"{self.base_url}/{self.game_name}/levels/{self.level}/postCommand"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        for add_data in self.add_commands_data:
            add_data = add_data.split('-')
            data = {"block_id": add_data[0], "dest_index": add_data[1]}
            response = requests.post(url, json=data, headers=headers)
            self.assertEqual(response.status_code, 200)
            block_data = response.json()
            self.assertIsNotNone(block_data["_id"])
            self.assertEqual(block_data["block"]["_id"], data["block_id"])

    def swap_commands(self):
        url = f"{self.base_url}/{self.game_name}/levels/{self.level}/swapCommand"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        former_solution = self.get_level_data()["solution"]
        for swap_data in self.swap_commands_data:
            swap_data = swap_data.split('-')
            dest = int(swap_data[1])
            src = int(swap_data[0])

            data = {"src_index": swap_data[0], "dest_index": swap_data[1]}
            response = requests.patch(url, json=data, headers=headers)
            self.assertEqual(response.status_code, 200)
            # check if jump and swing commands swapped
            new_solution = response.json()["solution"]
            self.assertEqual(new_solution[dest]["_id"], former_solution[src]["_id"])
            self.assertEqual(new_solution[src]["_id"], former_solution[dest]["_id"])
            former_solution = new_solution

    def solve_level(self):
        url = f"{self.base_url}/{self.game_name}/levels/solve/{self.level}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.patch(url, headers=headers)
        self.assertEqual(response.status_code, 200)
        level_data = response.json()
        self.assertTrue(level_data["solved"])

    def delete_commands(self):
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        former_solution = self.get_level_data()["solution"]
        self.delete_commands_data = [int(element) for element in self.delete_commands_data]
        i = 0
        while i < len(self.delete_commands_data):
            index = self.delete_commands_data[i]
            url = f"{self.base_url}/{self.game_name}/levels/{self.level}/deleteCommand/{index}"
            response = requests.delete(url, headers=headers)
            self.assertEqual(response.status_code, 200)
            new_solution = response.json()["solution"]
            if index < len(new_solution):
                self.assertNotEqual(new_solution[index]["_id"], former_solution[index]["_id"])
            former_solution = new_solution
            del self.delete_commands_data[i]
            self.delete_commands_data = [element - 1 if element > index else element for element in
                                         self.delete_commands_data]

    def restart_level(self):
        url = f"{self.base_url}/{self.game_name}/levels/restart/{self.level}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.patch(url, headers=headers)
        self.assertEqual(response.status_code, 200)
        new_level = response.json()
        self.assertEqual(new_level["solution"], [])
        self.assertFalse(new_level["solved"])

    def test_run(self):
        self.login()
        self.add_commands()
        self.swap_commands()
        self.solve_level()
        self.delete_commands()
        self.restart_level()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user_name', default='testing_user')
    parser.add_argument('--password', default='abcd1234')
    parser.add_argument('--test_directory', default='files')
    parser.add_argument('unittest_args', nargs='*')

    args = parser.parse_args()

    # Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
    sys.argv[1:] = args.unittest_args

    current_path = ''

    for root, dirs, files in os.walk(args.test_directory):
        for file_name in files:
            current_path = f'{args.test_directory}/{file_name}'
            suite = unittest.TestLoader().loadTestsFromTestCase(APITestCase)
            unittest.TextTestRunner().run(suite)
            time.sleep(1)
