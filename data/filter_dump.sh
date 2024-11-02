#!/bin/bash

# Check if input file is provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 input.sql output.sql"
    exit 1
fi

input_file=$1
output_file=$2

# Get the first 10 bill_ids
bill_ids=$(grep "INSERT INTO public.ls_bill" "$input_file" | head -n 10 | sed -E 's/.*\(([0-9]+),.*/\1/')

# Create a temporary file
temp_file=$(mktemp)

# Write the header portion (everything before first INSERT statement)
sed -n '1,/^COPY.*FROM stdin;$/p' "$input_file" > "$temp_file"

# For each table, only include relevant INSERT statements
{
    echo "-- Filtered to first 10 bills: $bill_ids"
    echo

    # ls_bill table - first 10 records
    echo "-- ls_bill records"
    grep "INSERT INTO public.ls_bill" "$input_file" | head -n 10

    echo
    echo "-- Related records from other tables"

    # For each bill_id, get related records
    for table in "ls_bill_amendment" "ls_bill_calendar" "ls_bill_history" "ls_bill_progress" \
                 "ls_bill_reason" "ls_bill_referral" "ls_bill_sast" "ls_bill_sponsor" \
                 "ls_bill_subject" "ls_bill_supplement" "ls_bill_text" "ls_bill_vote"; do
        echo
        echo "-- $table records"
        for id in $bill_ids; do
            grep "INSERT INTO public.$table" "$input_file" | grep "($id,"
        done
    done

    # Get vote details for related roll_call_ids
    echo
    echo "-- ls_bill_vote_detail records"
    roll_call_ids=$(grep "INSERT INTO public.ls_bill_vote" "$input_file" | grep -E "($bill_ids)" | sed -E 's/.*\(([0-9]+),.*/\1/')
    for id in $roll_call_ids; do
        grep "INSERT INTO public.ls_bill_vote_detail" "$input_file" | grep "($id,"
    done

    # Include all lookup/reference tables
    echo
    echo "-- Including all lookup/reference tables"
    for table in "ls_body" "ls_committee" "ls_event_type" "ls_mime_type" "ls_party" \
                "ls_people" "ls_progress" "ls_reason" "ls_role" "ls_sast_type" \
                "ls_session" "ls_sponsor_type" "ls_stance" "ls_state" "ls_subject" \
                "ls_supplement_type" "ls_text_type" "ls_type" "ls_variable" "ls_vote"; do
        echo
        echo "-- $table records"
        grep "INSERT INTO public.$table" "$input_file"
    done

} >> "$temp_file"

# Add any trailing commands (like ALTER TABLE statements)
grep -A 999999 "^ALTER TABLE" "$input_file" >> "$temp_file"

# Move temporary file to output
mv "$temp_file" "$output_file"

echo "Filtered SQL dump has been written to $output_file"