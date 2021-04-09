#!/bin/bash
__dirname=$(cd $(dirname "$0"); pwd -P)
cd "${__dirname}"

platform="Linux" # Assumed
uname=$(uname)
case $uname in
	"Darwin")
	platform="MacOS / OSX"
	;;
	MINGW*)
	platform="Windows"
	;;
esac

run(){
	echo $1
	eval $1
}

run_tests(){
    # If in a container, we run the actual test commands
    # otherwise we launch this command from the container
    if [[ -f /.dockerenv ]]; then
        echo "Running backend tests"
        run "python manage.py test"

        echo ""
        echo -e "\033[1mDone!\033[0m Everything looks in order."
    else
        echo "Running tests in webapp container"
        run "docker-compose exec webapp /bin/bash -c \"/webodm/webodm.sh test\""
    fi
}

run_tests
