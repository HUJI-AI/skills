#!/usr/bin/env bash
#
# hurcs-wiki.sh -- read the HURCS wiki (wiki.rcs.huji.ac.il), and only that wiki.
#
# The wiki is a Wiki.js site: a plain web fetch returns an empty JavaScript
# shell. This script identifies itself with its own User-Agent, lists pages through the wiki's public GraphQL endpoint and reads the
# server-rendered page text. The host is hard-coded, so the script cannot be
# pointed at any other site; that makes it safe to allow an agent to run it.
#
# Usage:
#   bash hurcs-wiki.sh list                 # every page: "<path>  --  <title>"
#   bash hurcs-wiki.sh search <term>        # pages whose path/title matches <term>
#   bash hurcs-wiki.sh read  <page-path>    # one page's text (HTML stripped)
#
# <page-path> is a wiki path like `hurcs/accounts/quota-management`
# (no scheme, no leading slash, no host). Needs bash and curl.

set -euo pipefail

readonly WIKI_HOST="wiki.rcs.huji.ac.il"
readonly WIKI_BASE="https://${WIKI_HOST}"
# Say what is asking. The wiki answers curl's default User-Agent with an error page.
readonly WIKI_UA="moriah-cluster-skill (HUJI AI portal; https://ai.huji.ac.il/)"
readonly WIKI_TIMEOUT=25

die() { printf 'hurcs-wiki: %s\n' "$1" >&2; exit 1; }

command -v curl >/dev/null 2>&1 || die "curl not found"

# Fetch a URL *under the wiki host only*. The path is always prefixed with the
# hard-coded base, so no caller input can redirect this to another host.
_get() {  # _get <path-under-base>
  curl -sS --max-time "$WIKI_TIMEOUT" -A "$WIKI_UA" "${WIKI_BASE}/$1"
}

# Turn a rendered wiki HTML page into readable text.
_strip_html() {
  # Drop <script>/<style> blocks first (they can span lines): join lines with
  # \001, mark each closing tag with \002, delete up to the mark, split again.
  # The mark is a literal byte, not "\x02", so BSD sed (macOS) works too.
  local m=$'\002'
  LC_ALL=C tr '\n' '\001' \
    | LC_ALL=C sed -e "s#</script>#${m}#g" -e "s/<script[^>]*>[^${m}]*${m}/ /g" \
          -e "s#</style>#${m}#g"  -e "s/<style[^>]*>[^${m}]*${m}/ /g" \
    | tr '\001' '\n' \
    | sed -e 's/<[^>]*>/ /g' \
      -e 's/&amp;/\&/g' -e 's/&quot;/"/g' -e "s/&#39;/'/g" \
      -e 's/&gt;/>/g' -e 's/&lt;/</g' -e 's/&nbsp;/ /g' \
    | tr -s ' \t' ' ' \
    | sed 's/^ *//' \
    | awk 'NF > 1'
}

# Print "<path>  --  <title>" for every page, via the public GraphQL endpoint.
_list_raw() {
  curl -sS --max-time "$WIKI_TIMEOUT" -A "$WIKI_UA" \
       -H "Content-Type: application/json" \
       -X POST "${WIKI_BASE}/graphql" \
       -d '{"query":"{pages{list(orderBy:PATH){path title}}}"}' \
  | tr '{' '\n' \
  | sed -n 's/.*"path":"\([^"]*\)".*"title":"\([^"]*\)".*/\1  --  \2/p'
}

cmd="${1:-}"
case "$cmd" in
  list)
    [[ $# -eq 1 ]] || die "usage: hurcs-wiki.sh list"
    _list_raw
    ;;
  search)
    [[ $# -eq 2 ]] || die "usage: hurcs-wiki.sh search <term>"
    _list_raw | grep -i -- "$2" || die "no page matches: $2"
    ;;
  read)
    [[ $# -eq 2 ]] || die "usage: hurcs-wiki.sh read <page-path>"
    path="$2"
    # Reject anything that could escape the wiki host or walk the URL.
    case "$path" in
      http://*|https://*|//*|/*)  die "give a wiki path like 'hurcs/accounts/quota-management', not a URL" ;;
    esac
    [[ "$path" == *".."* ]] && die "invalid path (contains '..'): $path"
    [[ "$path" =~ ^[A-Za-z0-9._/-]+$ ]] || die "invalid path characters: $path"
    _get "en/$path" | _strip_html
    ;;
  ""|-h|--help|help)
    sed -n '3,18p' "$0" | sed 's/^# \{0,1\}//'
    ;;
  *)
    die "unknown subcommand '$cmd' (try: list | search <term> | read <page-path>)"
    ;;
esac
