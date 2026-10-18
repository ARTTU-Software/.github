*** Settings ***
Documentation     Infrastructure smoke only. Does not load or verify board firmware.
Resource          ../renode.resource
Suite Setup       Setup
Suite Teardown    Teardown
Test Setup        Prepare Regression Test
Test Teardown     Finish Regression Test

*** Test Cases ***
Monitor Should Expose Commands
    [Tags]    infrastructure    smoke    case:monitor-help
    ${help}=    Execute Command    help
    Should Contain    ${help}    Available commands:
