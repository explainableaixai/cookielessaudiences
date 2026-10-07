#!/usr/bin/env bash
# Usage: COOKIELESS_KEY=... ./segment.sh https://example.com/blog
curl -s -X POST https://www.cookielessaudiences.com/api/audience/segment.php \
  -d "query=$1" -d "api_key=$COOKIELESS_KEY" -d 'format=structured'
