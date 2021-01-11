Contents
********

|

* `Steps on PrintNode`_
* `Steps on Odoo`_
* `Troubleshooting`_

|

==========================
 Quick configuration guide
==========================

|

Steps on PrintNode
##################

|

1. Sign up for `PrintNode <https://www.printnode.com/en>`_ to create a new account and generate an API key.
2. To use PrintNode you need to install and run the `PrintNode Client <https://www.printnode.com/en/download>`_ software on a computer connected to the internet and that has access to all your printers in your network (by default Pricing Plan PrintNode supports installation of the client on 3 different computers, but you can add more devices anytime)
3. Open API menu and copy `your API key <https://app.printnode.com/app/apikeys>`_ you will use later

|

.. image:: images/image11.png
   :width: 800px

|

Steps on Odoo
#############

|

4. Install the Odoo PrintNode app on your Odoo server
5. Go to PrintNode app > Configuration > Accounts > Click CREATE > Insert your API key copied from point 3 and click save

|

.. image:: images/image10.png
   :width: 800px

|

6. Click on Import printers button to get all printers from your PrinNode app
7. Go to user preferences and set up the default printer and “Print via PrintNode” checkbox (if the checkbox “Print via PrintNode” is set, then all documents will be auto-forwarded to Printer instead of downloading PDF)

|

.. image:: images/image7.png
   :width: 800px

|

8. This is it, now you can print directly on your default printers. Try to print any document and make sure your printer is switched on!

|

.. image:: images/image9.png
   :width: 800px

|

`TEST ON OUR SERVER > <https://odoo.ventor.tech/>`_

Our Demo server is recreated every day at 12.00 AM (UTC). So all your manually entered data will be deleted.

Troubleshooting
###############

|

If the system downloads reports instead of printing them, please check the checkbox ticked:

|

.. image:: images/image14.png
   :width: 800px
