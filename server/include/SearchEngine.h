#ifndef _SEARCHENGINE_H
#define _SEARCHENGINE_H

#include <vector>
#include <string>
#include <iostream>
#include <exception>

#include "HttpServer.h"


namespace SearchEngine {
	
	struct result {
		std::string filename;
		std::string tracker;
		std::string hash;
	};
	
	static std::vector<struct result> searchResults;
	
	
	std::vector<struct result> search(std::string searchTerm);
	
	std::vector<struct result> getResults();
	
	struct result getResultWithName(std::string filename);
}

#endif //_SEARCHENGINE_H