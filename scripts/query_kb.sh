#!/bin/bash
# US Customs Knowledge Base Query Helper
# Usage: ./scripts/query_kb.sh <command> [args]

API_BASE="http://localhost:8000"

case "$1" in
    search)
        # Search documents
        if [ -z "$2" ]; then
            echo "Usage: $0 search <query> [limit]"
            exit 1
        fi
        QUERY=$(echo "$2" | sed 's/ /%20/g')
        LIMIT="${3:-5}"
        curl -s "${API_BASE}/api/search?q=${QUERY}&limit=${LIMIT}" | python3 -m json.tool
        ;;

    hts)
        # Search HTS codes
        if [ -z "$2" ]; then
            echo "Usage: $0 hts <product> [limit]"
            exit 1
        fi
        QUERY=$(echo "$2" | sed 's/ /%20/g')
        LIMIT="${3:-10}"
        curl -s "${API_BASE}/api/hts/search?q=${QUERY}&limit=${LIMIT}" | python3 -m json.tool
        ;;

    hts-detail)
        # Get HTS code details
        if [ -z "$2" ]; then
            echo "Usage: $0 hts-detail <hts_number>"
            exit 1
        fi
        curl -s "${API_BASE}/api/hts/$2" | python3 -m json.tool
        ;;

    document)
        # Get document details
        if [ -z "$2" ]; then
            echo "Usage: $0 document <document_number>"
            exit 1
        fi
        curl -s "${API_BASE}/api/documents/$2" | python3 -m json.tool
        ;;

    status)
        # Get system status
        curl -s "${API_BASE}/api/status" | python3 -m json.tool
        ;;

    health)
        # Health check
        curl -s "${API_BASE}/health" | python3 -m json.tool
        ;;

    *)
        echo "US Customs Knowledge Base Query Tool"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  search <query> [limit]        Search customs documents"
        echo "  hts <product> [limit]         Search HTS tariff codes"
        echo "  hts-detail <hts_number>       Get HTS code details"
        echo "  document <doc_number>         Get document details"
        echo "  status                        Get system status"
        echo "  health                        Health check"
        echo ""
        echo "Examples:"
        echo "  $0 search 'steel antidumping duties' 5"
        echo "  $0 hts 'cheese' 10"
        echo "  $0 hts-detail '0406.10.00'"
        echo "  $0 document '2024-28582'"
        echo "  $0 status"
        exit 1
        ;;
esac
