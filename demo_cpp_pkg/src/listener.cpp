// std_msgs/String 구독자.
//
// 파라미터
//     log_prefix (string) : 로그 앞에 붙일 문구
//
// 토픽
//     chatter (std_msgs/String) : 구독. launch 에서 remapping 된다.

#include <cstddef>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class Listener : public rclcpp::Node
{
public:
  Listener()
  : Node("listener"), count_(0)
  {
    // declare_parameter 가 값을 바로 돌려준다. launch/params.yaml 이 기본값을 덮어쓴다.
    log_prefix_ = this->declare_parameter<std::string>("log_prefix", "heard");

    // 코드에는 상대 토픽명만 쓴다. 네임스페이스와 remapping 은 launch 가 정한다.
    sub_ = this->create_subscription<std_msgs::msg::String>(
      "chatter", 10,
      [this](const std_msgs::msg::String & msg) {
        ++count_;
        RCLCPP_INFO(
          this->get_logger(), "%s [%zu] -> \"%s\"",
          log_prefix_.c_str(), count_, msg.data.c_str());
      });

    RCLCPP_INFO(
      this->get_logger(), "listener 시작 | prefix='%s' | topic='%s'",
      log_prefix_.c_str(), sub_->get_topic_name());
  }

private:
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_;
  std::string log_prefix_;
  std::size_t count_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Listener>());
  rclcpp::shutdown();
  return 0;
}
