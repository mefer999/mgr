import mysql.connector


class SQL_handler():
    def __init__(self):
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="mefer",
                database="db_file"
            )
        except:
            print("Error")
        self.mycursor = self.db.cursor()

    def delete_user(self, t_name, u_name, u_surname):
        deleteQuery = "DELETE FROM " + t_name + " WHERE name = '" + \
            u_name + "' AND surname = '" + u_surname + "' ;"
        try:
            self.mycursor.execute(deleteQuery)
            self.db.commit()
            print("User deleted successfully")
        except:
            print("Cannot delete a user")

    def add_user(self, t_name, u_name, u_surname, u_idCard, status):
        addQuery = "INSERT INTO "+t_name + \
            " (name, surname, ID_card, status) VALUES (%(name)s,%(surname)s,%(ID_card)s,%(status)s)"
        insertData = {
            'name': u_name,
            'surname': u_surname,
            'ID_card': u_idCard,
            'status': status
        }
        try:
            self.mycursor.execute(addQuery, insertData)
            self.db.commit()
            print("User added successfully")
        except:
            print("Cannot add a user")

    def check_idCard(self, t_name, u_idCard):
        """returns name, surname and status if True, if False returns 0"""
        checkQuery = "SELECT IF(EXISTS (SELECT * FROM " + \
            t_name+" WHERE ID_card LIKE '%" + u_idCard+"%'), 1, 0)"
        self.mycursor.execute(checkQuery)
        ifExist = self.mycursor.fetchone()

        if ifExist[0] == 1:
            returnQuery = "SELECT name, surname, status FROM " + \
                t_name+" WHERE ID_card LIKE '%" + u_idCard+"%';"
            self.mycursor.execute(returnQuery)
            data = self.mycursor.fetchone()
            return data
        else:
            return 0

    def check_name(self, t_name, u_name, u_surname):
        checkQuery = "SELECT EXISTS(SELECT * FROM " + \
            t_name+" WHERE name LIKE '%" + u_name+"%' AND surname LIKE '%" + u_surname+"%')"
        self.mycursor.execute(checkQuery)
        ifExist = self.mycursor.fetchone()

        if ifExist[0] == 1:
            returnQuery = "SELECT name, surname, presence, status FROM " + \
                t_name+" WHERE name LIKE '%" + u_name+"%' AND surname LIKE '%" + u_surname+"%'"
            self.mycursor.execute(returnQuery)
            data = self.mycursor.fetchone()
            return data
        else:
            return 0

    def show_database(self, t_name):
        showQuery = "SELECT name, surname, ID_card, status, presence, personID FROM " + t_name+";"
        self.mycursor.execute(showQuery)
        for (name, surname, ID_card, status, presence, personID) in self.mycursor:
            print(
                f'{personID}. {name} {surname} | ID number: {ID_card} | {presence} | status: {status}')

    def change_presence(self, t_name, u_name, u_surname, u_presence):
        changeQuery = "UPDATE "+t_name+" SET presence='"+u_presence + \
            "' WHERE name LIKE '%"+u_name+"%' AND surname LIKE '%"+u_surname+"%'"
        self.mycursor.execute(changeQuery)

