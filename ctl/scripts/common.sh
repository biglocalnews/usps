. "$(dirname "$0")/db.sh"

export states="$1"

# Check if argument was missing
if [ -z "$states" ]; then
    echo "Pass in a comma separated list of states to load, e.g. 'CA,NV'. Pass 'all' to load everything."
    exit 1
fi

# Expand 'all'
if [ "$states" = "all" ]; then
    echo "Loading EVERY state!! This will take a very, very long time!"
    export states="AL,AK,AZ,AR,CA,CO,CT,DE,DC,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY"
fi

# Make sure to use upper case. TIGER scripts don't work otherwise.
export states=$(echo "$states" | tr '[:lower:]' '[:upper:]')
