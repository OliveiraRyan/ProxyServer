# Proxy Server

> Host Name: localhost  
> Default Port: 8888  

A localhost proxy server that intercepts all GET requests ran through it. Incorperates caching and HTML injection to display if a page was recieved from cache and how recent the page is.

While the proxy server is running, any request through localhost on port 8888 will be fetched and cached by the proxy server.

A page can be fetched by the proxy server on any web browser like so:  http://localhost:8888/the.web.page/to/visit/


## Warning!

The proxy server only works and has only been tested on Linux-based systems! It **does NOT** work on Windows because of how the OS views sockets with select.select [WinError 10038].

I have not tested on MacOS.


## TODO:

* There is a bug where the proxy server crashes on non UTF-8 encoded webpages.
* There is a bug where the favicon does not desplay
* Give an option for a user to set their preferred port through command line argument/flag
* Delete old cached files after a set *expiration date*
  * e.g. 1 week
  * Probably on application start-up
    * Can include an independent script that does it
    * Import the script into the main proxy<area>.py file

