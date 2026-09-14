#!/usr/bin/env bash
# lib/ui.sh - UI helpers and Card View renderer for bmh

# Terminal colors (if stdout is a tty)
if [[ -t 1 ]]; then
  BOLD="\033[1m"
  DIM="\033[2m"
  CYAN="\033[36m"
  GREEN="\033[32m"
  YELLOW="\033[33m"
  BLUE="\033[34m"
  MAGENTA="\033[35m"
  RESET="\033[0m"
else
  BOLD=""
  DIM=""
  CYAN=""
  GREEN=""
  YELLOW=""
  BLUE=""
  MAGENTA=""
  RESET=""
fi

render_banner() {
  echo -e "${BOLD}${CYAN}╭────────────────────────────────────────────────╮${RESET}" >&2
  echo -e "${BOLD}${CYAN}│  🧠 Basic Memory Helper (bmh)                  │${RESET}" >&2
  echo -e "${BOLD}${CYAN}│  ${DIM}Smart discovery & structured card inspector   ${RESET}${BOLD}${CYAN}│${RESET}" >&2
  echo -e "${BOLD}${CYAN}╰────────────────────────────────────────────────╯${RESET}" >&2
}

render_cards() {
  local json_input="$1"

  echo "$json_input" | jq -r '
    def to_rows:
      if type == "array" then
        if (.[0] | type) == "object" then .
        else map({value: .}) end
      elif type == "object" then
        ([to_entries[] | select(.value | type == "array" and (length > 0) and (.[0] | type == "object"))] | map(.value)) as $arr_fields
        | if ($arr_fields | length) > 0 then
            $arr_fields[0]
          else
            [.]
          end
      else
        [{value: .}]
      end;

    def format_date(val):
      if (val | type == "string") then
        (val | capture("(?<y>\\d{4})-(?<m>\\d{2})-(?<d>\\d{2})(?:[T\\s](?<H>\\d{2}):(?<M>\\d{2}))?") |
          "\(.d)/\(.m)/\(.y[2:])" + (if .H then " \(.H):\(.M)" else "" end)
        ) // val
      else
        val
      end;

    to_rows |
    if length == 0 then
      "No notes found matching criteria.\n"
    else
      length as $total |
      to_entries[] |
      .key as $idx |
      .value as $item |
      "╭─ " + ($item.title // $item.name // "Untitled Note") + " " + (if $total > 1 then "[\($idx+1)/\($total)] " else "" end) + "──────────────────────────────────────────\n\n" +
      (($item.content // $item.body // $item.description // "(No content)") | tostring) + "\n\n" +
      "├──────────────────────────────────────────────────────────────────────────\n" +
      (if $item.entity then "│ entity:      " + ($item.entity | tostring) + "\n" else "" end) +
      (if $item.external_id then "│ external_id: " + ($item.external_id | tostring) + "\n" else "" end) +
      "╰──────────────────────────────────────────────────────────────────────────\n"
    end
  '
}
