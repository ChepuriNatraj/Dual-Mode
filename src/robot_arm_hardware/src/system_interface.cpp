#include "robot_arm_hardware/system_interface.hpp"

#include <chrono>
#include <cmath>
#include <limits>
#include <memory>
#include <vector>
#include <sstream>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

namespace robot_arm_hardware
{

hardware_interface::CallbackReturn RobotArmSystemHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) != hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Retrieve parameters from URDF/ros2_control tag
  port_ = info_.hardware_parameters["port"];
  baud_rate_ = std::stoi(info_.hardware_parameters["baud_rate"]);

  hw_states_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());
  hw_commands_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());

  for (const hardware_interface::ComponentInfo & joint : info_.joints)
  {
    // Arm has command interface: position
    if (joint.command_interfaces[0].name != hardware_interface::HW_IF_POSITION)
    {
      RCLCPP_FATAL(rclcpp::get_logger("RobotArmSystemHardware"), "Joint '%s' has %s command interface found. '%s' expected.", joint.name.c_str(), joint.command_interfaces[0].name.c_str(), hardware_interface::HW_IF_POSITION);
      return hardware_interface::CallbackReturn::ERROR;
    }
    // Arm has state interface: position
    if (joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION)
    {
      RCLCPP_FATAL(rclcpp::get_logger("RobotArmSystemHardware"), "Joint '%s' has %s state interface found. '%s' expected.", joint.name.c_str(), joint.state_interfaces[0].name.c_str(), hardware_interface::HW_IF_POSITION);
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> RobotArmSystemHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;
  for (auto i = 0u; i < info_.joints.size(); i++)
  {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      info_.joints[i].name, hardware_interface::HW_IF_POSITION, &hw_states_[i]));
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> RobotArmSystemHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  for (auto i = 0u; i < info_.joints.size(); i++)
  {
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      info_.joints[i].name, hardware_interface::HW_IF_POSITION, &hw_commands_[i]));
  }

  return command_interfaces;
}

hardware_interface::CallbackReturn RobotArmSystemHardware::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("RobotArmSystemHardware"), "Activating ...please wait...");

  // Open Serial Port connection to Arduino/ESP8266
  serial_fd_ = open(port_.c_str(), O_RDWR | O_NOCTTY | O_NDELAY);
  if (serial_fd_ == -1) {
    RCLCPP_ERROR(rclcpp::get_logger("RobotArmSystemHardware"), "Unable to open port %s", port_.c_str());
    return hardware_interface::CallbackReturn::ERROR;
  }

  struct termios options;
  tcgetattr(serial_fd_, &options);
  cfsetispeed(&options, B115200);
  cfsetospeed(&options, B115200);
  options.c_cflag |= (CLOCAL | CREAD);
  tcsetattr(serial_fd_, TCSANOW, &options);

  // Set default initial values locally
  for (auto i = 0u; i < hw_states_.size(); i++)
  {
    if (std::isnan(hw_states_[i]))
    {
      hw_states_[i] = 0;
      hw_commands_[i] = 0;
    }
  }

  RCLCPP_INFO(rclcpp::get_logger("RobotArmSystemHardware"), "Successfully activated!");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RobotArmSystemHardware::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("RobotArmSystemHardware"), "Deactivating ...please wait...");
  close(serial_fd_);
  RCLCPP_INFO(rclcpp::get_logger("RobotArmSystemHardware"), "Successfully deactivated!");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type RobotArmSystemHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // For open loop physical arms (like standard MG996R without physical encoders), 
  // we cannot truly read the hardware state. We will simulate state by assigning command to state.
  // In a closed loop arm, you would read serial data in here from your Arduino.
  for (std::size_t i = 0; i < hw_states_.size(); i++)
  {
    hw_states_[i] = hw_commands_[i];
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type RobotArmSystemHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Build a comma-separated string of commands in DEGREES
  // Note: ROS uses Radians, so we convert rad -> deg mapping
  std::stringstream ss;
  
  // The calibrated home positions (0.0 rad in MoveIt = these degrees in hardware)
  double home_offsets[6] = {45.0, 0.0, 0.0, 45.0, 90.0, 0.0};

  for (std::size_t i = 0; i < hw_commands_.size(); i++)
  {
    // VERY Basic Radian -> Degree Conversion offset logic
    // Add the specific joint's calibration offset instead of 90.0
    double degrees = (hw_commands_[i] * 180.0 / M_PI) + home_offsets[i];
    
    // Clamp to [0, 180] for standard MG996R servos to prevent hardware stall/damage
    if (degrees < 0.0) degrees = 0.0;
    if (degrees > 180.0) degrees = 180.0;

    ss << static_cast<int>(degrees);
    
    if(i < hw_commands_.size() - 1){
      ss << ",";
    }
  }
  ss << "\n";
  
  std::string command_str = ss.str();
  ::write(serial_fd_, command_str.c_str(), command_str.length());

  return hardware_interface::return_type::OK;
}

}  // namespace robot_arm_hardware

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(
  robot_arm_hardware::RobotArmSystemHardware, hardware_interface::SystemInterface)
