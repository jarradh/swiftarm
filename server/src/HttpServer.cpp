#include "HttpServer.h"

namespace HttpServer {
	struct event_base *base;
	Download *test;
	Download *sg;
}

/**
 * Send the HTTP XML response.
 */
static void HttpServer::sendXMLResponse(struct evhttp_request *req, struct evbuffer *buf) {
	char speedstr[1024];
	sprintf(speedstr,"<DOWNLOADS><DOWNLOAD><NAME>bla!</NAME><DSPEED>%f</DSPEED><USPEED>%f</USPEED><PROGRESS>%f</PROGRESS></DOWNLOAD></DOWNLOADS>", 30.0, 20.0, 90.9);
	
	// Add HTTP headers.
	struct evkeyvalq *headers = evhttp_request_get_output_headers(req);
	evhttp_add_header(headers, "Content-Type", "text/xml" );
	
	// Add the XML message.
	int ret = evbuffer_add(buf, speedstr, strlen(speedstr));
	if (ret < 0) {
		printf("ERROR!");
		return;
	}
	
	// Send the final message.
	evhttp_send_reply(req, 200, "OK", buf);
	std::cout << "Sent the message." << std::endl;
}

/**
 * Send the HTTP response.
 */
static void HttpServer::sendResponse(struct evhttp_request *req, struct evbuffer *buf,  const char *message) {
	
	// Add HTTP headers.
	evhttp_add_header(evhttp_request_get_output_headers(req), "Content-Type", "text/plain");
	
	// Add the plaintext message with this.
	evbuffer_add_printf(buf,"%s", message);
	
	// Send the final message.
	evhttp_send_reply(req, 200, "OK", buf);
	std::cout << "Sent the message." << std::endl;
}

/**
 * The HTTP GET request handler.
 */
static void HttpServer::handleRequest(struct evhttp_request *req, void *arg) {
	
	const char *uri = evhttp_request_get_uri(req);
	const char *path;
	struct evbuffer *evb;
	struct evhttp_uri *decoded;
	
	std::cout << "Got a GET request for " << uri << std::endl;
	
	// Decode the URI.
	decoded = evhttp_uri_parse(uri);
	
	// This is the string we want to compare.
	path = evhttp_uri_get_path(decoded);
	std::string path_str = path;
	
	// This holds the content we want to send.
	evb = evbuffer_new();
	
	if(strcmp(path, "/download") == 0) {
		
		std::cout << "THE WRONG /DOWNLOAD" << std::endl;
		
		//std::string tracker   = "130.161.158.52:20000";
		std::string hash   = "367d26a6ce626e049a21921100e24eac86dbcd32";
		
		try {
			DownloadManager::switchDownload(hash);
			sendResponse(req, evb, "Download Started");
		}
		catch(FileNotFoundException e) {
			std::cout << "Exception Caught In HttpServer" << std::endl;
			std::cout << e.what() << std::endl;
			sendResponse(req, evb, "-1");
			
		}
		
	//Temporarily hard coded.
	} else if(strcmp(path, "/add2") == 0) {
		std::string tracker     = "127.0.0.1:20000";
		std::string root_hash   = "367d26a6ce626e049a21921100e24eac86dbcd32";
		std::string name        = "SG.mkv";
		sg        = new Download(tracker, root_hash, name);
		
		DownloadManager::add(sg);
		
		//DownloadManager::startDownload(test->getRootHash());
		//TODO: Construct the path where the file will be downloaded.
		char response[] = "Added SG download";
		
		sendResponse(req, evb, response);
	
	//Temporarily hard coded.
	} else if(strcmp(path, "/add1") == 0) {
		std::string tracker     = "127.0.0.1:20000";
		std::string root_hash   = "012b5549e2622ea8bf3d694b4f55c959539ac848";
		std::string name        = "bla.mp4";
		test                    = new Download(tracker, root_hash, name);
		
		DownloadManager::add(test);
		
		//DownloadManager::startDownload(test->getRootHash());
		//TODO: Construct the path where the file will be downloaded.
		char response[] = "Added test download";
		
		sendResponse(req, evb, response);
	
	// The realm not hard coded version of /add.
	} else if(path_str.size() >= 4 && path_str.substr(0, 5).compare("/add") == 0) {
		
		if(path_str.size() > 5 && path_str.at(4) == ':'){
			
			std::string filename = path_str.substr(5, path_str.size());
			
			try {
				struct SearchEngine::result res = SearchEngine::getResultWithName(filename);
				test = new Download(res.tracker, res.hash, res.filename);
				
				DownloadManager::add(test);
				
				sendResponse(req, evb, "Download Added");
			}
			catch(FileNotFoundException e) {
				std::cout << "Exception Caught In HttpServer" << std::endl;
				std::cout << e.what() << std::endl;
				sendResponse(req, evb, "-1");
				
			}
		}
	
	//Temporarily hard coded.
	} else if (strcmp(path, "/resume") == 0) {
		std::string root_hash   = "012b5549e2622ea8bf3d694b4f55c959539ac848";
		std::cout << "Resuming Download: " << DownloadManager::resumeDownload(root_hash) << std::endl;
		
		char response[] = "Resumed Download";
		sendResponse(req, evb, response);
		
	//Temporarily hard coded.
	} else if (strcmp(path, "/pause") == 0) {
		std::string root_hash   = "012b5549e2622ea8bf3d694b4f55c959539ac848";
		DownloadManager::pauseDownload(root_hash);
		
		char response[] = "Paused Current Download.";
		sendResponse(req, evb, response);
		
	// This will be the real (not hard coded) version of /download
	// Message will look like: "/download:filename"
	} else if(path_str.size() >= 9 && path_str.substr(0, 9).compare("/download") == 0) {
		
		if(path_str.size() > 10 && path_str.at(9) == ':'){
			
			std::string hash = path_str.substr(10, path_str.size());
			try {
				DownloadManager::switchDownload(hash);
				sendResponse(req, evb, "Download Started");
			}
			catch(FileNotFoundException e) {
				std::cout << "Exception Caught In HttpServer" << std::endl;
				std::cout << e.what() << std::endl;
				sendResponse(req, evb, "-1");
				
			}
		}
		
		/**
		 * SEARCH
		 */
	} else if(path_str.size() >= 7 && path_str.substr(0, 7).compare("/search") == 0) {
		
		if(path_str.size() > 8 && path_str.at(7) == ':') {
			
			std::string searchTerm = path_str.substr(8, path_str.size());
			
			SearchEngine::search(searchTerm);
			
			sendResponse(req, evb, "Search Complete");
			
		} else {
			sendResponse(req, evb, "Invalid Search Term");
		}
		
	} else if (strcmp(path, "/getDownloads") == 0) {
		sendXMLResponse(req, evb);
		
	} else if (strcmp(path, "/stream") == 0) {
		
		std::string tracker     = "127.0.0.1:20000";
		DownloadManager::startStream(tracker);
		
		//TODO: Construct url from which stream can be read from.
		sendResponse(req, evb, "http://127.0.0.1:15000/012b5549e2622ea8bf3d694b4f55c959539ac848");
		
	// This will be the real (not hard coded) version of /stream
	// Message will look like: "/stream:filename"
	} else if (path_str.size() >= 7 && path_str.substr(0,7).compare("/stream") == 0) {
		
		if(path_str.size() > 8 && path_str.at(7) == ':') {
			
			std::string filename = path_str.substr(8, path_str.size());
			
			try {
				struct SearchEngine::result res = SearchEngine::getResultWithName(filename);
				
				DownloadManager::startStream(res.tracker);
				
				std::string address = "http://127.0.0.1:15000/" + res.hash;
				
				sendResponse(req, evb, address.c_str());
				
			}
			catch(FileNotFoundException e) {
				std::cout << "Exception Caught In HttpServer" << std::endl;
				sendResponse(req, evb, e.what());
				
			}
		}
		
	} else if (strcmp(path, "/progress") == 0) {
		double progress = test->getStatistics().download_percentage;
		char response[8];
		sprintf(response, "%f", progress);
		
		sendResponse(req, evb, response);
		
	} else if (strcmp(path, "/alive") == 0) {
		sendResponse(req, evb, "Alive");
		
	} else if (strcmp(path, "/close") == 0) {
		DownloadManager::stopStream();
		sendResponse(req, evb, "Not streaming anymore.");
		
	} else {
		std::cout << "Bad request: " << path << std::endl;
	}
	
	// Some garbage collecting.
	if (decoded) {
		evhttp_uri_free(decoded);
		std::cout << "Cleaned decoded garbage" << std::endl;
	}
	if (evb) {
		evbuffer_free(evb);
		std::cout << "Cleaned evb garbage" << std::endl;
	}
}

/**
 * Initialize the web server.
 */
int HttpServer::init() {
	struct evhttp *http;
	struct evhttp_bound_socket *handle;
	
	// The port we want to bind.
	unsigned short port = 1337;
	
	// The event base.
	base = event_base_new();
	std::cout << "Created new event base." << std::endl;
	
	// Create a new evhttp object to handle requests.
	http = evhttp_new(base);
	std::cout << "Created new evhttp." << std::endl;
	
	// Assign the request handler to the web server.
	evhttp_set_gencb(http, handleRequest, NULL);
	
	// Now we tell the evhttp what port to listen on.
	handle = evhttp_bind_socket_with_handle(http, "127.0.0.1", port);
	//handle = evhttp_bind_socket_with_handle(http, "130.161.159.107", port);
	if (!handle) {
		std::cerr << "Couldn't bind to port " << (int)port << ". Exiting." << std::endl;
		return 1;
	} else {
		std::cout << "Successfully bound to port " << (int)port << "." << std::endl;
	}
	
	// Go into the main loop.
	event_base_dispatch(base);
	
	return 0;
}

