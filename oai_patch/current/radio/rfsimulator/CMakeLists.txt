# SPDX-License-Identifier: LicenseRef-CSSL-1.0

add_compile_options(-Wunused-parameter)
add_library(rfsimulator MODULE
            simulator.cpp
            apply_channelmod.c
            stk_channel_model.c
            stk_trace.c
            stk_schedule.c
            stk_trace_channel.c
            qd_channel_reader.c
            qd_channel_adapter.c
            ../../openair1/PHY/TOOLS/signal_energy.c
)
target_link_libraries(rfsimulator PRIVATE SIMU log_headers crypto)
set_target_properties(rfsimulator PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

add_executable(replay_node stored_node.c)
target_link_libraries (replay_node minimal_lib)
