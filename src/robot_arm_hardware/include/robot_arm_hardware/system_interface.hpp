#ifndef ROBOT_ARM_HARDWARE__SYSTEM_INTERFACE_HPP_
#define ROBOT_ARM_HARDWARE__SYSTEM_INTERFACE_HPP_

#include <vector>
#include <string>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "rclcpp_lifecycle/state.hpp"

namespace robot_arm_hardware
{

class RobotArmSystemHardware : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(RobotArmSystemHardware)

  hardware_interface::CallbackReturn on_init(const hardware_interface::HardwareInfo & info) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  hardware_interface::CallbackReturn on_activate(const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_deactivate(const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::return_type read(const rclcpp::Time & time, const rclcpp::Duration & period) override;

  hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  // Communication config
  std::string port_;
  int baud_rate_;
  int serial_fd_; // file descriptor for pure C++ serial or use a serial library

  // Dummy vectors for holding position/velocity state and commands for our 6 DOF arm
  std::vector<double> hw_commands_;
  std::vector<double> hw_states_;
  
  // Custom function to send commands over serial
  bool send_serial_command(const std::vector<double>& commands);
};

}  // namespace robot_arm_hardware

#endif  // ROBOT_ARM_HARDWARE__SYSTEM_INTERFACE_HPP_
