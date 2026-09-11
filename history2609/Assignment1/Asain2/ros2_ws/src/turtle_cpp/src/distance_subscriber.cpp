#include <functional>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"

class DistanceSubscriber : public rclcpp::Node
{
public:
    DistanceSubscriber()
        : Node("distance_subscriber")pytest 통과 출력 — 작성한 테스트 3개의 의도
    {
        RCLCPP_INFO(
            this->get_logger(),
            "Distance subscriber started"
        );

        subscription_ = this->create_subscription<std_msgs::msg::Float32>(
            "/turtle_distance",
            10,
            std::bind(
                &DistanceSubscriber::distance_callback,
                this,
                std::placeholders::_1
            )
        );
    }

private:
    void distance_callback(
        const std_msgs::msg::Float32::SharedPtr msg)
    {
        RCLCPP_INFO(
            this->get_logger(),
            "[rclcpp Subscriber] Received distance: %.2f",
            msg->data
        );
    }

    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);

    auto node = std::make_shared<DistanceSubscriber>();

    rclcpp::spin(node);
    rclcpp::shutdown();

    return 0;
}